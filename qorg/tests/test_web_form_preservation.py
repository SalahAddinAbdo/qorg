"""Regression tests preventing upgrades from overwriting Web Form customizations."""

import unittest
from types import SimpleNamespace

from qorg.qorg.enterprise_foundation.web_form_preservation import preserve_existing_web_form


class FakeMeta:
    def __init__(self, fields):
        self.fields = set(fields)

    def has_field(self, fieldname):
        return fieldname in self.fields


class FakeDoc(SimpleNamespace):
    pass


class TestWebFormPreservation(unittest.TestCase):
    def test_existing_configuration_is_not_changed(self):
        doc = FakeDoc(
            meta=FakeMeta({"qorg_managed_update_available", "qorg_managed_version"}),
            qorg_managed_update_available=0,
            qorg_managed_version="3.0.0",
            title="Locally Customized Form",
            custom_css=".user-rule { color: red; }",
            client_script="console.log('local');",
            web_form_fields=[{"fieldname": "email", "reqd": 0, "label": "Local label"}],
        )
        preserved = {
            "title": doc.title,
            "custom_css": doc.custom_css,
            "client_script": doc.client_script,
            "web_form_fields": list(doc.web_form_fields),
        }
        self.assertEqual(preserve_existing_web_form(doc, "4.0.0"), "preserved")
        self.assertEqual(doc.qorg_managed_update_available, 1)
        self.assertEqual(doc.qorg_managed_version, "3.0.0")
        for fieldname, value in preserved.items():
            self.assertEqual(getattr(doc, fieldname), value)

    def test_missing_management_version_may_be_initialized(self):
        doc = FakeDoc(
            meta=FakeMeta({"qorg_managed_update_available", "qorg_managed_version"}),
            qorg_managed_update_available=0,
            qorg_managed_version=None,
        )
        preserve_existing_web_form(doc, "4.0.0")
        self.assertEqual(doc.qorg_managed_version, "4.0.0")
        self.assertEqual(doc.qorg_managed_update_available, 1)


if __name__ == "__main__":
    unittest.main()
