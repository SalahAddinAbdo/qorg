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
        self._apply_safe_defaults()
        self._compose_full_name_when_missing()
        self._bind_authenticated_portal_owner()

    def validate(self):
        validate_external_person(self)
        update_profile_metrics(self)

    def on_update(self):
        self.db_set("last_profile_update", now_datetime(), update_modified=False)

    def _apply_safe_defaults(self):
        self.person_status = self.person_status or "Active"

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

    def _bind_authenticated_portal_owner(self):
        user = frappe.session.user
        if not user or user == "Guest" or not _is_web_form_request():
            return

        if not self.is_new() and self.user and self.user != user:
            frappe.throw(_("You can only update your own external profile."), frappe.PermissionError)

        duplicate = frappe.db.get_value(
            "External Person",
            {"user": user, "name": ["!=", self.name or ""]},
            "name",
        )
        if duplicate:
            frappe.throw(
                _("An external profile already exists for this account: {0}").format(duplicate)
            )

        self.user = user
        if self.is_new():
            self.source = "Portal Registration"
        if self.get("privacy_consent"):
            self.privacy_consent_on = self.privacy_consent_on or now_datetime()
            self.privacy_consent_source = (
                self.privacy_consent_source or "External Profile Portal"
            )


def _is_web_form_request() -> bool:
    request = getattr(frappe.local, "request", None)
    path = getattr(request, "path", "") or ""
    command = frappe.form_dict.get("cmd") if getattr(frappe.local, "form_dict", None) else None
    return (
        "frappe.website.doctype.web_form.web_form.accept" in path
        or command == "frappe.website.doctype.web_form.web_form.accept"
        or path.startswith("/external-profile-form")
    )


def resolve_external_person_for_user(user: str | None, *, repair=True):
    if not user or user == "Guest" or not frappe.db.exists("DocType", "External Person"):
        return None

    direct = frappe.db.get_value("External Person", {"user": user}, "name")
    if direct:
        return frappe.get_doc("External Person", direct)

    # Recover profiles created by the same authenticated account before portal
    # ownership binding was corrected. Owner is preferred over email matching.
    candidates = frappe.get_all(
        "External Person",
        filters={"owner": user, "user": ["is", "not set"]},
        pluck="name",
        limit_page_length=2,
    )

    if not candidates:
        email = frappe.db.get_value("User", user, "email") or user
        candidates = frappe.get_all(
            "External Person",
            filters={"primary_email": email, "user": ["is", "not set"]},
            pluck="name",
            limit_page_length=2,
        )

    if len(candidates) != 1:
        return None

    name = candidates[0]
    if repair:
        frappe.db.set_value(
            "External Person",
            name,
            {"user": user, "source": "Portal Registration"},
            update_modified=False,
        )
        frappe.clear_document_cache("External Person", name)
    return frappe.get_doc("External Person", name)


def reconcile_unlinked_external_profiles():
    repaired = []
    ambiguous = []
    rows = frappe.get_all(
        "External Person",
        filters={"user": ["is", "not set"]},
        fields=["name", "owner", "primary_email"],
        limit_page_length=0,
    )
    for row in rows:
        users = []
        if row.owner and row.owner != "Guest" and frappe.db.exists("User", row.owner):
            users = [row.owner]
        elif row.primary_email:
            users = frappe.get_all(
                "User",
                filters={"email": row.primary_email, "enabled": 1},
                pluck="name",
                limit_page_length=2,
            )
        if len(users) == 1:
            frappe.db.set_value(
                "External Person",
                row.name,
                {"user": users[0], "source": "Portal Registration"},
                update_modified=False,
            )
            repaired.append(row.name)
        elif len(users) > 1:
            ambiguous.append(row.name)
    return {"repaired": repaired, "ambiguous": ambiguous}
