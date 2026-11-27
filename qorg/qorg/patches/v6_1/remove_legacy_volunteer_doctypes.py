import frappe
from frappe import _

LEGACY=("Volunteer Engagement","Volunteer Application","Volunteer Profile")

def execute():
    for doctype in LEGACY:
        if not frappe.db.exists("DocType", doctype):
            continue
        count=frappe.db.count(doctype)
        if count:
            frappe.throw(_("Cannot remove {0}: {1} record(s) still exist. Delete them explicitly, then rerun migrate.").format(doctype,count))
        frappe.delete_doc("DocType",doctype,force=True,ignore_permissions=True)
    for report in ("Volunteer Application Pipeline",):
        if frappe.db.exists("Report",report):frappe.delete_doc("Report",report,force=True,ignore_permissions=True)
    frappe.clear_cache()
