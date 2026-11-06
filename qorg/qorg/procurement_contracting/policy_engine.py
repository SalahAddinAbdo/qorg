from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Iterable, Optional

from .decimal_utils import decimal
from .exceptions import ConfigurationError, PolicyResolutionError


@dataclass(frozen=True)
class PolicyContext:
    company: str
    currency: str
    procurement_type: str
    estimated_value: Decimal
    transaction_date: date
    risk_level: Optional[str] = None
    project: Optional[str] = None
    donor: Optional[str] = None
    item_group: Optional[str] = None
    emergency: bool = False


@dataclass(frozen=True)
class PolicyRule:
    name: str
    company: str
    currency: str
    procurement_type: str
    minimum_amount: Decimal
    maximum_amount: Optional[Decimal]
    procurement_method: str
    priority: int = 0
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    risk_level: Optional[str] = None
    project: Optional[str] = None
    donor: Optional[str] = None
    item_group: Optional[str] = None
    emergency_only: bool = False
    disabled: bool = False
    requirements: dict = field(default_factory=dict)

    def __post_init__(self):
        object.__setattr__(self, "minimum_amount", decimal(self.minimum_amount, "minimum_amount"))
        if self.maximum_amount not in (None, ""):
            object.__setattr__(self, "maximum_amount", decimal(self.maximum_amount, "maximum_amount"))
        if self.maximum_amount is not None and self.maximum_amount < self.minimum_amount:
            raise ConfigurationError(f"{self.name}: maximum_amount cannot be less than minimum_amount")

    def specificity(self):
        return sum(bool(x) for x in (self.risk_level, self.project, self.donor, self.item_group)) + int(self.emergency_only)

    def matches(self, c: PolicyContext):
        if self.disabled:
            return False
        if (self.company, self.currency, self.procurement_type) != (c.company, c.currency, c.procurement_type):
            return False
        if c.estimated_value < self.minimum_amount:
            return False
        if self.maximum_amount is not None and c.estimated_value > self.maximum_amount:
            return False
        if self.effective_from and c.transaction_date < self.effective_from:
            return False
        if self.effective_to and c.transaction_date > self.effective_to:
            return False
        if self.emergency_only and not c.emergency:
            return False
        for attr in ("risk_level", "project", "donor", "item_group"):
            configured = getattr(self, attr)
            if configured and configured != getattr(c, attr):
                return False
        return True


def _same_scope(a: PolicyRule, b: PolicyRule):
    fields = ("company", "currency", "procurement_type", "risk_level", "project", "donor", "item_group", "emergency_only")
    return all(getattr(a, f) == getattr(b, f) for f in fields)


def _dates_overlap(a: PolicyRule, b: PolicyRule):
    start_a = a.effective_from or date.min
    end_a = a.effective_to or date.max
    start_b = b.effective_from or date.min
    end_b = b.effective_to or date.max
    return max(start_a, start_b) <= min(end_a, end_b)


def _amounts_overlap(a: PolicyRule, b: PolicyRule):
    end_a = a.maximum_amount if a.maximum_amount is not None else Decimal("Infinity")
    end_b = b.maximum_amount if b.maximum_amount is not None else Decimal("Infinity")
    return max(a.minimum_amount, b.minimum_amount) <= min(end_a, end_b)


def validate_no_ambiguous_overlap(rules: Iterable[PolicyRule]):
    active = [r for r in rules if not r.disabled]
    conflicts = []
    for i, left in enumerate(active):
        for right in active[i + 1:]:
            if (_same_scope(left, right) and _dates_overlap(left, right) and _amounts_overlap(left, right)
                    and left.priority == right.priority):
                conflicts.append((left.name, right.name))
    if conflicts:
        pairs = ", ".join(f"{a} <> {b}" for a, b in conflicts)
        raise ConfigurationError(f"Ambiguous procurement policy overlap: {pairs}")
    return True


def resolve_policy(context: PolicyContext, rules: Iterable[PolicyRule]):
    candidates = [r for r in rules if r.matches(context)]
    if not candidates:
        raise PolicyResolutionError("No active procurement policy rule matches the request")
    candidates.sort(key=lambda r: (r.specificity(), r.priority, r.effective_from or date.min), reverse=True)
    winner = candidates[0]
    if len(candidates) > 1:
        second = candidates[1]
        key1 = (winner.specificity(), winner.priority, winner.effective_from or date.min)
        key2 = (second.specificity(), second.priority, second.effective_from or date.min)
        if key1 == key2:
            raise PolicyResolutionError(f"Policy resolution is ambiguous between {winner.name} and {second.name}")
    return {
        "rule": winner.name,
        "method": winner.procurement_method,
        "requirements": dict(winner.requirements),
        "reason": f"Matched {winner.company}/{winner.currency}/{winner.procurement_type} at value {context.estimated_value}",
    }
