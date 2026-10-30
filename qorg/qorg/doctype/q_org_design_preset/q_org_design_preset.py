from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now

from qorg.qorg.design_system import DESIGN_SYSTEM_SCHEMA_VERSION
from qorg.qorg.design_system.service import fingerprint, validate_values, values_from


class QOrgDesignPreset(Document):
    def validate(self) -> None:
        validate_values(self)
        self.schema_version = DESIGN_SYSTEM_SCHEMA_VERSION
        self.configuration_fingerprint = fingerprint(
            values_from(self, with_defaults=False)
        )
        self.validation_status = "Valid"
        self.last_validated_on = now()
        self._validate_standard_preset_access()

    def _validate_standard_preset_access(self) -> None:
        """Protect managed standard presets without blocking provisioning.

        Runtime role checks use ``frappe.get_roles(user)``. Internal provisioning is explicitly allowed
        through ``ignore_permissions`` so first install and migration can create
        the managed standard presets safely.
        """
        if not self.is_standard:
            return

        if self.flags.ignore_permissions:
            return

        if frappe.session.user == "Administrator":
            return

        roles = set(frappe.get_roles(frappe.session.user) or [])
        if "System Manager" not in roles:
            frappe.throw(
                _("Only Administrator or a System Manager can modify a standard design preset."),
                frappe.PermissionError,
            )
