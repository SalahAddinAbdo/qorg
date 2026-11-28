from __future__ import annotations

import frappe
from frappe import _

LEGACY_DOCTYPE = "Procurement Complaint"
LEGACY_TEMPLATE = "Procurement Complaint Acknowledgement"


def remove_legacy_procurement_complaint_artifacts():
    """Idempotently remove non-DocType legacy records after the source model is retired.

    Frappe removes the Standard DocType itself as an orphan during migrate after its
    source directory is deleted. This hook refuses cleanup if legacy data or files
    still exist, then removes obsolete template/configuration records only.
    """
    if frappe.db.exists("DocType", LEGACY_DOCTYPE):
        record_count = frappe.db.count(LEGACY_DOCTYPE)
        file_count = frappe.db.count("File", {"attached_to_doctype": LEGACY_DOCTYPE})
        if record_count or file_count:
            frappe.throw(
                _("Cannot retire {0}: {1} records and {2} attached files remain.").format(
                    LEGACY_DOCTYPE, record_count, file_count
                )
            )

    removed = []
    for doctype, filters in (
        ("Email Template", {"name": LEGACY_TEMPLATE}),
        ("Notification", {"document_type": LEGACY_DOCTYPE}),
        ("Client Script", {"dt": LEGACY_DOCTYPE}),
        ("Server Script", {"reference_doctype": LEGACY_DOCTYPE}),
    ):
        if not frappe.db.exists("DocType", doctype):
            continue
        for name in frappe.get_all(doctype, filters=filters, pluck="name"):
            frappe.delete_doc(doctype, name, ignore_permissions=True, force=True)
            removed.append(f"{doctype}:{name}")

    frappe.clear_cache()
    return {"ok": True, "legacy_doctype": LEGACY_DOCTYPE, "removed": removed}
