from __future__ import annotations
import frappe

OLD_WORKSPACES=("QFap Management Hub","Project Cycle Management")
OLD_SIDEBARS=("QFap Adds",)
OLD_ICONS=("QFap Adds","QFap Management Hub")

OWNED_APPS = ("", None, "qorg", "qfap_adds")


def _is_owned_legacy_workspace(name):
    """Delete only legacy records that belong to this application family.

    A workspace that carries a legacy name but belongs to a Module Def of another
    app (or was created for another module) must never be removed by migrate.
    """
    module = frappe.db.get_value("Workspace", name, "module")
    if not module:
        return True
    return frappe.db.get_value("Module Def", module, "app_name") in OWNED_APPS


def prepare_q_org_identity():
    for name in OLD_WORKSPACES:
        if name != "Q Management Hub" and frappe.db.exists("Workspace",name) and _is_owned_legacy_workspace(name):
            frappe.delete_doc("Workspace",name,ignore_permissions=True,force=True)
    for name in OLD_SIDEBARS:
        if name != "Q Org" and frappe.db.exists("Workspace Sidebar",name):
            frappe.delete_doc("Workspace Sidebar",name,ignore_permissions=True,force=True)
    for name in OLD_ICONS:
        if name != "Q Org" and frappe.db.exists("Desktop Icon",name):
            frappe.delete_doc("Desktop Icon",name,ignore_permissions=True,force=True)
    frappe.clear_cache()
