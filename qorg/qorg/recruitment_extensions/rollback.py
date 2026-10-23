from __future__ import annotations
import frappe
MANAGED_PREFIX="qorg_"
@frappe.whitelist()
def preview():
    if frappe.session.user!="Administrator":frappe.throw("Administrator is required.",frappe.PermissionError)
    fields=frappe.get_all("Custom Field",filters={"module":"QOrg","fieldname":["like",MANAGED_PREFIX+"%"]},fields=["name","dt","fieldname"])
    used=[]
    for row in fields:
        count=frappe.db.count(row.dt,{row.fieldname:["is","set"]}) if frappe.db.exists("DocType",row.dt) else 0
        if count:used.append({**row,"records_with_data":count})
    return {"managed_fields":fields,"fields_with_data":used,"safe_to_remove":not used}
@frappe.whitelist(methods=["POST"])
def disable_extension():
    if frappe.session.user!="Administrator":frappe.throw("Administrator is required.",frappe.PermissionError)
    return {"disabled":False,"message":"Disable Extended Recruitment through Feature Control Center. No data or managed fields were deleted."}
