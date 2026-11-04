from __future__ import annotations

import unittest

import frappe

from qorg.qorg.doctype.managed_configuration_state.managed_configuration_state import (
    is_internal_managed_state_write,
    managed_state_write,
)


class TestEnterpriseFoundationCriticalCleanup(unittest.TestCase):
    def test_managed_state_context_is_scoped(self):
        self.assertFalse(is_internal_managed_state_write())
        with managed_state_write():
            self.assertTrue(is_internal_managed_state_write())
        self.assertFalse(is_internal_managed_state_write())

    def test_managed_state_context_restores_existing_value(self):
        frappe.flags.qorg_managed_configuration_state_write = True
        try:
            with managed_state_write():
                self.assertTrue(is_internal_managed_state_write())
            self.assertTrue(is_internal_managed_state_write())
        finally:
            frappe.flags.qorg_managed_configuration_state_write = False
