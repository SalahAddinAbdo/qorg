"""Source-only checks for QOrg DocType metadata and form safety."""

import json
import unittest
from pathlib import Path


DOCTYPE_ROOT = Path(__file__).resolve().parents[1] / "qorg" / "doctype"
LAYOUT_FIELDS = {"Section Break", "Column Break", "Tab Break", "HTML", "Heading", "Button", "Fold"}


class TestDocTypeMetadataIntegrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.definitions = []
        for path in DOCTYPE_ROOT.glob("*/*.json"):
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict) and data.get("doctype") == "DocType":
                cls.definitions.append((path, data))

    def test_field_order_matches_defined_fields(self):
        errors = []
        for path, data in self.definitions:
            names = [field.get("fieldname") for field in data.get("fields", []) if field.get("fieldname")]
            order = data.get("field_order", [])
            if len(order) != len(set(order)) or set(names) != set(order):
                errors.append(str(path))
        self.assertFalse(errors, f"Invalid field_order metadata: {errors}")

    def test_hidden_or_layout_fields_are_not_list_columns_or_filters(self):
        errors = []
        for path, data in self.definitions:
            for field in data.get("fields", []):
                invalid = field.get("hidden") or field.get("fieldtype") in LAYOUT_FIELDS
                if invalid and (field.get("in_list_view") or field.get("in_standard_filter")):
                    errors.append(f"{data.get('name')}.{field.get('fieldname')} ({path})")
        self.assertFalse(errors, f"Invalid list/filter fields: {errors}")

    def test_dynamic_links_and_fetch_sources_exist(self):
        errors = []
        for path, data in self.definitions:
            names = {field.get("fieldname") for field in data.get("fields", [])}
            for field in data.get("fields", []):
                if field.get("fieldtype") == "Dynamic Link" and field.get("options") not in names:
                    errors.append(f"{data.get('name')}.{field.get('fieldname')}: Dynamic Link")
                if field.get("fetch_from") and field["fetch_from"].split(".", 1)[0] not in names:
                    errors.append(f"{data.get('name')}.{field.get('fieldname')}: fetch_from")
        self.assertFalse(errors, f"Broken metadata references: {errors}")

    def test_generated_integrity_fields_are_protected(self):
        expected = {
            ("Procurement Process", "frozen_hash"): (True, True, True),
            ("Cost Distribution Ledger", "source_hash"): (True, True, True),
            ("Cost Distribution Ledger", "target_snapshot"): (True, True, False),
            ("Managed Configuration State", "applied_fingerprint"): (True, True, False),
            ("Managed Configuration State", "last_seen_fingerprint"): (True, True, False),
            ("Shared Cost Allocation Run", "rule_snapshot"): (True, True, False),
        }
        actual = {}
        for _, data in self.definitions:
            for field in data.get("fields", []):
                key = (data.get("name"), field.get("fieldname"))
                if key in expected:
                    actual[key] = (
                        bool(field.get("read_only")),
                        bool(field.get("print_hide")),
                        bool(field.get("hidden")),
                    )
        self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()
