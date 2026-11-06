import frappe
from frappe import _


def route_material_request(doc, method=None):
    if doc.docstatus != 1:
        return
    if not frappe.db.exists("DocType", "Procurement and Contracting Settings"):
        return
    settings = frappe.get_single("Procurement and Contracting Settings")
    request_type = doc.material_request_type
    if request_type == "Purchase":
        target = settings.default_procurement_officer or settings.default_logistics_officer
        subject = _("Approved purchase request requires procurement action")
    elif request_type in ("Material Transfer", "Material Issue"):
        target = settings.default_stock_manager
        subject = _("Approved stock request requires warehouse action")
    else:
        return
    if not target:
        frappe.log_error(_("No default responsible user configured for Material Request {0}").format(doc.name), "QOrg Procurement Routing")
        return
    if frappe.db.exists("DocField", {"parent": "Material Request", "fieldname": "custom_current_responsible_user"}):
        doc.db_set("custom_current_responsible_user", target, update_modified=False)
    frappe.get_doc({
        "doctype": "ToDo",
        "allocated_to": target,
        "reference_type": "Material Request",
        "reference_name": doc.name,
        "description": subject,
        "priority": "Medium",
        "status": "Open",
    }).insert(ignore_permissions=True)
