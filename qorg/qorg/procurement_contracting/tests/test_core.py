import unittest
from datetime import date
from decimal import Decimal

from qorg.qorg.procurement_contracting.committee_engine import CommitteeMandate, CommitteeMember, quorum_met, resolve_committee
from qorg.qorg.procurement_contracting.evaluation_engine import (
    financial_score, individual_average, individual_then_consensus,
    measured_value_to_score, validate_component_weights, weighted_member_average,
)
from qorg.qorg.procurement_contracting.exceptions import CommitteeError, ConfigurationError, EvaluationError, PolicyResolutionError
from qorg.qorg.procurement_contracting.policy_engine import PolicyContext, PolicyRule, resolve_policy, validate_no_ambiguous_overlap


class PolicyTests(unittest.TestCase):
    def rule(self, name, minimum, maximum, method, priority=0, **kwargs):
        return PolicyRule(name, "QOrg", "USD", "Goods", minimum, maximum, method, priority=priority, **kwargs)

    def context(self, value, **kwargs):
        return PolicyContext("QOrg", "USD", "Goods", Decimal(str(value)), date(2026, 11, 6), **kwargs)

    def test_boundary_is_inclusive(self):
        result = resolve_policy(self.context(1000), [self.rule("R1", 0, 1000, "Direct")])
        self.assertEqual(result["method"], "Direct")

    def test_no_match(self):
        with self.assertRaises(PolicyResolutionError):
            resolve_policy(self.context(1001), [self.rule("R1", 0, 1000, "Direct")])

    def test_specific_rule_wins(self):
        generic = self.rule("Generic", 0, 5000, "RFQ")
        project = self.rule("Project", 0, 5000, "Restricted", project="P-1")
        self.assertEqual(resolve_policy(self.context(100, project="P-1"), [generic, project])["rule"], "Project")

    def test_priority_wins(self):
        low = self.rule("Low", 0, 5000, "RFQ", priority=1)
        high = self.rule("High", 0, 5000, "Restricted", priority=2)
        self.assertEqual(resolve_policy(self.context(100), [low, high])["rule"], "High")

    def test_overlap_rejected(self):
        with self.assertRaises(ConfigurationError):
            validate_no_ambiguous_overlap([self.rule("A", 0, 1000, "Direct"), self.rule("B", 1000, 2000, "RFQ")])


class EvaluationTests(unittest.TestCase):
    def test_component_weights(self):
        self.assertEqual(validate_component_weights([{"weight": 70}, {"weight": 30}]), Decimal("100"))

    def test_bad_component_weights(self):
        with self.assertRaises(ValueError):
            validate_component_weights([{"weight": 60}, {"weight": 30}])

    def test_individual_average(self):
        rows = [{"score": 80, "submitted": True}, {"score": 70, "submitted": True}, {"score": 90, "submitted": True}]
        self.assertEqual(individual_average(rows, 3), Decimal("80.0000"))

    def test_excluded_score_not_counted(self):
        rows = [{"score": 80, "submitted": True}, {"score": 0, "submitted": True, "excluded": True}]
        self.assertEqual(individual_average(rows), Decimal("80.0000"))

    def test_weighted_members(self):
        rows = [{"score": 80, "member_weight": 40, "submitted": True}, {"score": 90, "member_weight": 60, "submitted": True}]
        self.assertEqual(weighted_member_average(rows), Decimal("86.0000"))

    def test_consensus_deviation_needs_detail(self):
        rows = [{"score": 50, "submitted": True}, {"score": 50, "submitted": True}]
        with self.assertRaises(EvaluationError):
            individual_then_consensus(rows, 90, True, "short", 10)

    def test_financial_formula(self):
        self.assertEqual(financial_score(90000, 100000), Decimal("90.0000"))

    def test_measured_band(self):
        bands = [{"minimum": 0, "maximum": 7, "score": 100}, {"minimum": 8, "maximum": 14, "score": 80}]
        self.assertEqual(measured_value_to_score(10, bands), Decimal("80.0000"))


class CommitteeTests(unittest.TestCase):
    def mandate(self):
        members = (
            CommitteeMember("a@example.com", "Chair"),
            CommitteeMember("b@example.com", "Member"),
            CommitteeMember("c@example.com", "Member"),
        )
        return CommitteeMandate("TC-1", "Technical", "QOrg", date(2026, 1, 1), date(2027, 12, 31), 2, members)

    def test_resolve_committee(self):
        m = resolve_committee([self.mandate()], "Technical", company="QOrg", amount=1000, procurement_type="Goods", project=None, on_date=date(2026, 11, 6))
        self.assertEqual(m.name, "TC-1")

    def test_quorum(self):
        self.assertTrue(quorum_met(self.mandate(), ["a@example.com", "b@example.com"]))
        self.assertFalse(quorum_met(self.mandate(), ["a@example.com"]))

    def test_expired_committee(self):
        with self.assertRaises(CommitteeError):
            resolve_committee([self.mandate()], "Technical", company="QOrg", amount=1000, procurement_type="Goods", project=None, on_date=date(2028, 1, 1))


if __name__ == "__main__":
    unittest.main()


def test_rfq_extension_sources_are_integrated():
    from pathlib import Path
    root = Path(__file__).resolve().parents[4]
    provisioning = (root / "qorg/qorg/procurement_contracting/provisioning.py").read_text()
    guards = (root / "qorg/qorg/procurement_contracting/standard_guards.py").read_text()
    hooks = (root / "qorg/hooks.py").read_text()
    for fieldname in ("custom_contact_employee", "custom_submission_deadline", "custom_delivery_location", "custom_bid_security_required", "custom_site_visit_required", "custom_required_documents"):
        assert fieldname in provisioning
    assert "validate_rfq_extensions(doc)" in guards
    assert "public/js/request_for_quotation.js" in hooks
    assert "procurement_inventory_v2" not in hooks
