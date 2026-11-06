from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from .decimal_utils import decimal, require_exact_hundred
from .exceptions import CommitteeError


@dataclass(frozen=True)
class CommitteeMember:
    user: str
    role: str
    voting: bool = True
    alternate_for: str | None = None
    member_weight: Decimal | None = None
    recused: bool = False
    active: bool = True


@dataclass(frozen=True)
class CommitteeMandate:
    name: str
    committee_type: str
    company: str
    valid_from: date
    valid_to: date
    quorum: int
    members: tuple
    minimum_amount: Decimal | None = None
    maximum_amount: Decimal | None = None
    procurement_type: str | None = None
    project: str | None = None
    disabled: bool = False

    def is_valid_on(self, on_date):
        return not self.disabled and self.valid_from <= on_date <= self.valid_to

    def supports(self, *, company, amount, procurement_type=None, project=None, on_date=None):
        if not self.is_valid_on(on_date or date.today()) or self.company != company:
            return False
        amount = decimal(amount)
        if self.minimum_amount is not None and amount < decimal(self.minimum_amount):
            return False
        if self.maximum_amount is not None and amount > decimal(self.maximum_amount):
            return False
        if self.procurement_type and self.procurement_type != procurement_type:
            return False
        if self.project and self.project != project:
            return False
        return True


def resolve_committee(mandates, committee_type, **context):
    matches = [m for m in mandates if m.committee_type == committee_type and m.supports(**context)]
    if not matches:
        raise CommitteeError(f"No active {committee_type} committee mandate matches the process")
    if len(matches) > 1:
        raise CommitteeError(f"Multiple active {committee_type} committee mandates match the process")
    validate_mandate(matches[0])
    return matches[0]


def validate_mandate(mandate):
    eligible = [m for m in mandate.members if m.active and m.voting and not m.recused and not m.alternate_for]
    if mandate.quorum < 1:
        raise CommitteeError("Committee quorum must be at least one")
    if mandate.quorum > len(eligible):
        raise CommitteeError("Committee quorum exceeds eligible voting members")
    weights = [m.member_weight for m in eligible if m.member_weight is not None]
    if weights:
        if len(weights) != len(eligible):
            raise CommitteeError("All eligible voting members need weights when weighted voting is enabled")
        require_exact_hundred(weights, "committee member weights")
    return True


def quorum_met(mandate, attending_users):
    validate_mandate(mandate)
    attendees = set(attending_users)
    count = sum(1 for m in mandate.members if m.user in attendees and m.active and m.voting and not m.recused)
    return count >= mandate.quorum
