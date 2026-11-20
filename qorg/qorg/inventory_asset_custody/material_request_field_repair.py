from __future__ import annotations
import frappe

def repair_material_request_issue_fields():
    condition='eval:doc.material_request_type == "Material Issue" && doc.custom_recipient_type == "Employee"'
    name=frappe.db.get_value("Custom Field",{"dt":"Material Request","fieldname":"custom_recipient_employee"},"name")
    if name:
        frappe.db.set_value("Custom Field",name,{"depends_on":condition,"mandatory_depends_on":condition},update_modified=False)
    frappe.clear_cache(doctype="Material Request")
