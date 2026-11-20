from __future__ import annotations

import frappe

DOCTYPE = "Cost Distribution Profile"
MANAGER_ROLES = ("Accounts Manager", "Projects Manager")


def repair_profile_submit_permissions():
    """Repair existing DocPerm rows without saving the Standard DocType.

    Saving a Standard DocType invokes Frappe's developer-mode guard. During
    after_migrate we only need to update the child DocPerm records that were
    synchronized from the app JSON, so update those records directly.
    """
    if not frappe.db.exists("DocType", DOCTYPE):
        return

    repaired = 0
    missing_roles = []

    for role in MANAGER_ROLES:
        permission_name = frappe.db.get_value(
            "DocPerm",
            {"parent": DOCTYPE, "parenttype": "DocType", "role": role},
            "name",
        )

        if not permission_name:
            missing_roles.append(role)
            continue

        frappe.db.set_value(
            "DocPerm",
            permission_name,
            {"submit": 1, "cancel": 1, "amend": 1},
            update_modified=False,
        )
        repaired += 1

    # The permission rows are owned by the standard DocType JSON and should
    # already exist after schema synchronization. Fail clearly if the JSON was
    # not uploaded or synchronized instead of mutating the Standard DocType.
    if missing_roles:
        frappe.throw(
            "Missing Cost Distribution Profile permission rows for: "
            + ", ".join(missing_roles)
            + ". Upload the complete cost_distribution_profile.json and rerun migrate."
        )

    frappe.clear_cache(doctype=DOCTYPE)
    return {"repaired": repaired, "roles": list(MANAGER_ROLES)}
