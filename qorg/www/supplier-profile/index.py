import frappe

from qorg.qorg.procurement_contracting.portal_workflow import supplier_profile_path


def get_context(context):
    if frappe.session.user == "Guest":
        frappe.local.flags.redirect_location = "/login?redirect-to=/supplier-profile"
    else:
        frappe.local.flags.redirect_location = supplier_profile_path()
    raise frappe.Redirect
