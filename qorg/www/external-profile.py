import frappe
def get_context(context):
    if frappe.session.user=="Guest": frappe.throw("Login required",frappe.PermissionError)
    name=frappe.form_dict.get("person"); user=frappe.session.user
    if name:
        doc=frappe.get_doc("External Person",name)
        if doc.user!=user and user!="Administrator": frappe.throw("Not permitted",frappe.PermissionError)
    else:
        name=frappe.db.get_value("External Person",{"user":user},"name")
        doc=frappe.get_doc("External Person",name) if name else None
    context.no_cache=1; context.person=doc; context.title="My Professional Profile"
