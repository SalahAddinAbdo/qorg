"""Source-only checks for standard QOrg report metadata."""

import json
import unittest
from pathlib import Path


REPORT_ROOT = Path(__file__).resolve().parents[1] / "qorg" / "report"


class TestReportMetadataIntegrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reports = []
        for path in REPORT_ROOT.glob("*/*.json"):
            data = json.loads(path.read_text(encoding="utf-8"))
            cls.reports.append((path, data))

    def test_every_report_has_reference_doctype_and_roles(self):
        errors = []
        for path, report in self.reports:
            if not report.get("ref_doctype") or not report.get("roles"):
                errors.append(str(path))
        self.assertFalse(errors, f"Incomplete report access metadata: {errors}")

    def test_participation_reports_have_operational_roles(self):
        required = {
            "Participation Performance",
            "Completion and Exit Tracking",
            "Participation Hours and Completion",
            "Onboarding and Clearance Status",
            "Application Screening and Aging",
            "Active Engagements",
            "Assessment Progress",
            "Participation Pipeline",
        }
        expected_roles = {"System Manager", "Volunteer Manager", "Volunteer Coordinator"}
        errors = []
        for path, report in self.reports:
            if report.get("name") not in required:
                continue
            roles = {row.get("role") for row in report.get("roles", [])}
            if roles != expected_roles:
                errors.append(f"{path}: {sorted(roles)}")
        self.assertFalse(errors, f"Invalid participation-report roles: {errors}")

    def test_roles_are_unique_and_nonempty(self):
        errors = []
        for path, report in self.reports:
            roles = [row.get("role") for row in report.get("roles", [])]
            if not all(roles) or len(roles) != len(set(roles)):
                errors.append(str(path))
        self.assertFalse(errors, f"Invalid report role rows: {errors}")


if __name__ == "__main__":
    unittest.main()
