from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from qorg.qorg.enterprise_foundation.permissions import (
    feature_control_center_has_permission,
    is_administrator,
    managed_state_has_permission,
    require_administrator,
)


class TestEnterpriseFoundationPermissions(FrappeTestCase):
    def test_administrator_only_helpers(self):
        self.assertTrue(is_administrator("Administrator"))
        self.assertTrue(feature_control_center_has_permission(user="Administrator"))
        self.assertTrue(managed_state_has_permission(user="Administrator"))
        self.assertFalse(is_administrator("test@example.com"))
        self.assertFalse(feature_control_center_has_permission(user="test@example.com"))
        self.assertFalse(managed_state_has_permission(user="test@example.com"))

    def test_require_administrator_rejects_other_users(self):
        with patch(
            "qorg.qorg.enterprise_foundation.permissions.is_administrator",
            return_value=False,
        ):
            with self.assertRaises(frappe.PermissionError):
                require_administrator()

    def test_feature_control_center_has_no_role_docperm(self):
        path = Path(frappe.get_app_path(
            "qorg", "qorg", "doctype", "feature_control_center", "feature_control_center.json"
        ))
        payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(payload.get("permissions"), [])
