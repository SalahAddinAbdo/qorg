import frappe
from frappe import _
def get_context(context):
    if frappe.session.user == "Guest": frappe.throw(_("Login required"), frappe.PermissionError)
    profile=frappe.db.get_value("Supplier Registration",{"owner":frappe.session.user},["supplier"],as_dict=True) or {}
    context.contracts=frappe.get_all("Contract",filters={"party_type":"Supplier","party_name":profile.get("supplier")},fields=["name","qorg_contract_title","qorg_lifecycle_status","end_date","qorg_contract_value"]) if profile.get("supplier") else []
    return context
