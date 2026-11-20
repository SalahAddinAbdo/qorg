"""Completeness checks for field properties that intentionally use framework defaults."""

import json
import unittest
from pathlib import Path


APP_ROOT = Path(__file__).resolve().parents[1]
DOCTYPE_ROOT = APP_ROOT / "qorg" / "doctype"
POLICY_PATH = APP_ROOT / "metadata" / "field_property_policy.json"


class TestFieldPropertyPolicy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
        cls.definitions = []
        for path in DOCTYPE_ROOT.glob("*/*.json"):
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict) and data.get("doctype") == "DocType":
                cls.definitions.append((path, data))

    def test_every_currency_field_has_source_or_explicit_policy(self):
        policy_keys = {
            (row["doctype"], row["fieldname"])
            for row in self.policy["currency_fields_without_options"]
        }
        actual_keys = {
            (data["name"], field["fieldname"])
            for _, data in self.definitions
            for field in data.get("fields", [])
            if field.get("fieldtype") == "Currency" and not field.get("options")
        }
        self.assertEqual(actual_keys, policy_keys)

    def test_links_have_targets(self):
        missing = []
        for path, data in self.definitions:
            for field in data.get("fields", []):
                if field.get("fieldtype") in {"Link", "Table", "Table MultiSelect"} and not field.get("options"):
                    missing.append(f"{data['name']}.{field.get('fieldname')} ({path})")
        self.assertFalse(missing, f"Relational fields without targets: {missing}")

    def test_required_fields_are_not_conditionally_hidden(self):
        conflicts = []
        for path, data in self.definitions:
            for field in data.get("fields", []):
                if field.get("reqd") and field.get("depends_on") and not field.get("mandatory_depends_on"):
                    conflicts.append(f"{data['name']}.{field.get('fieldname')} ({path})")
        self.assertFalse(conflicts, f"Required fields can become hidden: {conflicts}")

    def test_policy_entries_are_complete(self):
        allowed = {"framework_default_no_company_context", "hidden_mixed_currency_diagnostic"}
        invalid = [
            row for row in self.policy["currency_fields_without_options"]
            if row.get("resolution") not in allowed or not row.get("reason")
        ]
        self.assertFalse(invalid, f"Incomplete policy decisions: {invalid}")


if __name__ == "__main__":
    unittest.main()
