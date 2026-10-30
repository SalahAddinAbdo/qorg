from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime

from qorg.qorg.people_and_opportunities.services.people import (
    update_profile_metrics,
    validate_external_person,
)


class ExternalPerson(Document):
    def before_validate(self):
        self._apply_portal_defaults()
        self._compose_full_name_when_missing()

    def validate(self):
        validate_external_person(self)
        update_profile_metrics(self)

    def on_update(self):
        self.db_set("last_profile_update", now_datetime(), update_modified=False)

    def _compose_full_name_when_missing(self):
        if self.get("full_name"):
            self.full_name = self.full_name.strip()
            return
        parts = [
            (self.get(fieldname) or "").strip()
            for fieldname in ("first_name", "middle_name", "last_name")
        ]
        composed = " ".join(part for part in parts if part)
        if composed:
            self.full_name = composed

    def _apply_portal_defaults(self):
        self.person_status = self.person_status or "Active"
        user = frappe.session.user
        if not user or user == "Guest":
            return
        if frappe.db.get_value("User", user, "user_type") != "Website User":
            return
        if not self.is_new() and self.user and self.user != user:
            frappe.throw(_("You can only update your own external profile."), frappe.PermissionError)
        duplicate = frappe.db.get_value(
            "External Person",
            {"user": user, "name": ["!=", self.name or ""]},
            "name",
        )
        if duplicate:
            frappe.throw(_("An external profile already exists for this account: {0}").format(duplicate))
        self.user = user
        if self.is_new():
            self.source = "Portal Registration"
        if self.get("privacy_consent"):
            self.privacy_consent_on = self.privacy_consent_on or now_datetime()
            self.privacy_consent_source = self.privacy_consent_source or "External Profile Portal"
