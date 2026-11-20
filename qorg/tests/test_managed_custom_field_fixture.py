from __future__ import annotations

import json
import unittest
from pathlib import Path


class TestManagedCustomFieldFixture(unittest.TestCase):
    def setUp(self):
        app_root = Path(__file__).resolve().parents[1]
        fixture_path = app_root / "fixtures" / "custom_field.json"
        self.records = json.loads(fixture_path.read_text(encoding="utf-8"))

    def test_fixture_records_have_qorg_ownership(self):
        violations = []
        for record in self.records:
            if record.get("doctype") != "Custom Field":
                continue
            if record.get("module") != "QOrg" or record.get("is_system_generated") != 1:
                violations.append(record.get("name") or record.get("fieldname"))

        self.assertFalse(
            violations,
            "Managed Custom Fields must use module=QOrg and is_system_generated=1: "
            + ", ".join(violations),
        )

    def test_fixture_names_match_doctype_and_fieldname(self):
        violations = []
        for record in self.records:
            if record.get("doctype") != "Custom Field":
                continue
            expected_name = f"{record.get('dt')}-{record.get('fieldname')}"
            if record.get("name") != expected_name:
                violations.append(f"{record.get('name')} != {expected_name}")

        self.assertFalse(violations, "Invalid Custom Field fixture names: " + "; ".join(violations))


if __name__ == "__main__":
    unittest.main()
