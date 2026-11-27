from __future__ import annotations

import re
import unicodedata

import frappe
from frappe import _

_DIGIT_TRANSLATION = str.maketrans(
    "٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹",
    "01234567890123456789",
)


def _ascii_digits(value):
    return unicodedata.normalize("NFKC", value or "").translate(_DIGIT_TRANSLATION)


def normalize_email(value):
    return (value or "").strip().casefold()


def normalize_mobile(value):
    value = _ascii_digits(value).strip()
    leading_plus = value.startswith("+")
    digits = re.sub(r"\D", "", value)
    return ("+" if leading_plus and digits else "") + digits


def normalize_identity(value):
    value = _ascii_digits(value).strip().upper()
    return re.sub(r"[^0-9A-Z]", "", value)


def identity_matches(doc, *, exclude_name=None):
    current_name = exclude_name or doc.name or ""
    matches = {}
    if doc.get("user"):
        names = frappe.get_all(
            "External Person",
            filters={"user": doc.user, "name": ["!=", current_name]},
            pluck="name",
        )
        if names:
            matches["user"] = names
    for fieldname, value in (
        ("primary_email", normalize_email(doc.get("primary_email"))),
        ("mobile_no", normalize_mobile(doc.get("mobile_no"))),
    ):
        if not value:
            continue
        names = frappe.get_all(
            "External Person",
            filters={fieldname: value, "person_status": ["!=", "Merged"], "name": ["!=", current_name]},
            pluck="name",
        )
        if names:
            matches[fieldname] = names
    official_id = normalize_identity(doc.get("identification_number"))
    if official_id and doc.get("identification_type"):
        filters = {
            "identification_type": doc.identification_type,
            "identification_number": official_id,
            "name": ["!=", current_name],
        }
        if doc.get("identification_country"):
            filters["identification_country"] = doc.identification_country
        names = frappe.get_all("External Person", filters=filters, pluck="name")
        if names:
            matches["official_identity"] = names
    return matches


def validate_identity_uniqueness(doc, config):
    enabled = {
        "user": True,
        "primary_email": bool(config.match_by_email),
        "mobile_no": bool(config.match_by_mobile),
        "official_identity": bool(config.match_by_official_id),
    }
    conflicts = {key: names for key, names in identity_matches(doc).items() if enabled.get(key)}
    if conflicts:
        details = "; ".join(f"{key}: {', '.join(names)}" for key, names in sorted(conflicts.items()))
        frappe.throw(
            _("Potential duplicate External Person detected. Resolve the matching records before saving: {0}").format(details)
        )
