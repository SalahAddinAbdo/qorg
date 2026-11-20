"""Regression tests for managed Web Form and source DocField alignment."""

import json
import unittest
from pathlib import Path
from types import SimpleNamespace

from qorg.qorg.enterprise_foundation.web_form_field_sync import (
    synchronize_web_form_field,
)
from qorg.qorg.people_and_opportunities.web_form_definitions import WEB_FORMS


APP_ROOT = Path(__file__).resolve().parents[1]
DOCTYPE_ROOT = APP_ROOT / "qorg" / "doctype"


class FakeMeta:
    def __init__(self, supported):
        self.supported = set(supported)

    def has_field(self, fieldname):
        return fieldname in self.supported


class FakeRow:
    def __init__(self):
        self.values = {}

    def set(self, fieldname, value):
        self.values[fieldname] = value


class TestWebFormFieldSync(unittest.TestCase):
    def test_source_mandatory_and_conditional_properties_are_authoritative(self):
        target = SimpleNamespace(
            fieldname="primary_email",
            fieldtype="Data",
            label="Primary Email",
            options="Email",
            description="Contact address",
            default=None,
            depends_on="eval:doc.contact_allowed",
            mandatory_depends_on="eval:!doc.mobile_no",
            read_only_depends_on=None,
            reqd=0,
            read_only=0,
        )
        supported = {
            "fieldname", "fieldtype", "label", "options", "description", "default",
            "depends_on", "mandatory_depends_on", "read_only_depends_on", "reqd",
            "req", "read_only",
        }
        row = FakeRow()
        synchronize_web_form_field(
            row,
            FakeMeta(supported),
            target,
            {"required": True},  # A stale layout hint must not override DocField.reqd.
        )
        self.assertEqual(row.values["reqd"], 0)
        self.assertEqual(row.values["req"], 0)
        self.assertEqual(row.values["mandatory_depends_on"], "eval:!doc.mobile_no")
        self.assertEqual(row.values["depends_on"], "eval:doc.contact_allowed")

    def test_source_read_only_is_preserved_and_portal_may_be_stricter(self):
        target = SimpleNamespace(
            fieldname="status", fieldtype="Select", label="Status", options="Draft\nSubmitted",
            description=None, default="Draft", depends_on=None, mandatory_depends_on=None,
            read_only_depends_on=None, reqd=1, read_only=0,
        )
        supported = {"fieldname", "fieldtype", "label", "options", "description", "default",
                     "reqd", "req", "read_only"}
        row = FakeRow()
        synchronize_web_form_field(row, FakeMeta(supported), target, {"read_only": True})
        self.assertEqual(row.values["reqd"], 1)
        self.assertEqual(row.values["read_only"], 1)

    def test_local_web_form_fields_exist_in_source_doctypes(self):
        definitions = {}
        for path in DOCTYPE_ROOT.glob("*/*.json"):
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict) and data.get("doctype") == "DocType":
                definitions[data["name"]] = data
        missing = []
        hidden = []
        for form in WEB_FORMS:
            source = definitions.get(form["doc_type"])
            if not source:  # Standard ERPNext/HRMS DocTypes are verified at provisioning time.
                continue
            fields = {field["fieldname"]: field for field in source.get("fields", [])}
            for item in form["layout"]:
                fieldname = item.get("fieldname")
                if not fieldname:
                    continue
                if fieldname not in fields:
                    missing.append(f"{form['title']}: {fieldname}")
                elif fields[fieldname].get("hidden"):
                    hidden.append(f"{form['title']}: {fieldname}")
        self.assertFalse(missing, f"Web Form fields missing from source DocTypes: {missing}")
        self.assertFalse(hidden, f"Hidden source fields exposed by Web Forms: {hidden}")


if __name__ == "__main__":
    unittest.main()
