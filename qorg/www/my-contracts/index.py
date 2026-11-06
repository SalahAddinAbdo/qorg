import frappe
from frappe import _
def get_context(context):
    if frappe.session.user == "Guest": frappe.throw(_("Login required"), frappe.PermissionError)
    profile=frappe.db.get_value("Supplier Registration",{"owner":frappe.session.user},["supplier"],as_dict=True) or {}
    context.contracts=frappe.get_all("Procurement Contract",filters={"supplier":profile.get("supplier")},fields=["name","contract_title","status","end_date","contract_value"]) if profile.get("supplier") else []
    return context
