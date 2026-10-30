from __future__ import annotations

import frappe


def get_context(context):
    context.no_cache = 1
    if frappe.session.user == "Guest":
        frappe.local.flags.redirect_location = "/login?redirect-to=/external-profile-form"
    else:
        frappe.local.flags.redirect_location = "/external-profile-form"
    raise frappe.Redirect
