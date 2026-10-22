from __future__ import annotations

import frappe


def remove_legacy_print_settings():
    """Remove the obsolete settings DocType after Print Settings has been provisioned.

    This runs after migration. Data is already copied by provision_print_settings.
    The child rule DocType remains because Print Settings uses it directly.
    """
    legacy_doctype = "QFAP Print Format Settings"
    if not frappe.db.exists("DocType", legacy_doctype):
        return
    # Do not remove until the replacement fields exist.
    if not frappe.get_meta("Print Settings").has_field("qorg_rules"):
        return
    frappe.delete_doc("DocType", legacy_doctype, ignore_permissions=True, force=True)
    frappe.clear_cache()
