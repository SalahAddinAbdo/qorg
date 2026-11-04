from __future__ import annotations

import uuid

import frappe
from frappe.tests.utils import FrappeTestCase

from qorg.qorg.doctype.managed_configuration_state.managed_configuration_state import (
    is_internal_managed_state_write,
    managed_state_write,
)
from qorg.qorg.enterprise_foundation.workflow_manager import _save_state


class TestManagedConfigurationState(FrappeTestCase):
    def setUp(self):
        frappe.set_user("Administrator")
        self.key = f"Assurance::{uuid.uuid4().hex}"

    def tearDown(self):
        if frappe.db.exists("Managed Configuration State", self.key):
            with managed_state_write():
                frappe.delete_doc(
                    "Managed Configuration State",
                    self.key,
                    ignore_permissions=True,
                    force=True,
                )
        frappe.set_user("Administrator")

    def _new_state(self):
        return frappe.get_doc({
            "doctype": "Managed Configuration State",
            "component_key": self.key,
            "component_type": "Other",
            "managed_version": "assurance-1",
            "management_status": "Managed",
        })

    def test_internal_context_is_scoped_and_restored(self):
        self.assertFalse(is_internal_managed_state_write())
        with managed_state_write():
            self.assertTrue(is_internal_managed_state_write())
            with managed_state_write():
                self.assertTrue(is_internal_managed_state_write())
            self.assertTrue(is_internal_managed_state_write())
        self.assertFalse(is_internal_managed_state_write())

    def test_manual_insert_is_rejected_even_with_ignore_permissions(self):
        with self.assertRaises(frappe.PermissionError):
            self._new_state().insert(ignore_permissions=True)

    def test_internal_insert_update_and_delete_are_allowed(self):
        with managed_state_write():
            doc = self._new_state().insert(ignore_permissions=True)
        doc.management_status = "Administrator Modified"
        with managed_state_write():
            doc.save(ignore_permissions=True)
        self.assertEqual(
            frappe.db.get_value("Managed Configuration State", self.key, "management_status"),
            "Administrator Modified",
        )
        with managed_state_write():
            frappe.delete_doc(
                "Managed Configuration State",
                self.key,
                ignore_permissions=True,
                force=True,
            )
        self.assertFalse(frappe.db.exists("Managed Configuration State", self.key))

    def test_workflow_manager_write_is_allowed_and_idempotent(self):
        _save_state(
            self.key,
            "assurance-1",
            "desired-a",
            "actual-a",
            "Managed",
            {"run": 1},
        )
        _save_state(
            self.key,
            "assurance-1",
            "desired-a",
            "actual-b",
            "Managed",
            {"run": 2},
        )
        self.assertEqual(
            frappe.db.count("Managed Configuration State", {"component_key": self.key}),
            1,
        )
        state = frappe.get_doc("Managed Configuration State", self.key)
        self.assertEqual(state.applied_fingerprint, "actual-b")
        self.assertEqual(frappe.parse_json(state.details), {"run": 2})

    def test_manual_update_and_delete_are_rejected(self):
        with managed_state_write():
            doc = self._new_state().insert(ignore_permissions=True)
        doc.management_status = "Administrator Modified"
        with self.assertRaises(frappe.PermissionError):
            doc.save(ignore_permissions=True)
        with self.assertRaises(frappe.PermissionError):
            frappe.delete_doc(
                "Managed Configuration State",
                self.key,
                ignore_permissions=True,
                force=True,
            )
