import frappe
def status_summary(doctype,status_field="status"):
    rows=frappe.db.sql(f"select `{status_field}` label,count(*) value from `tab{doctype}` group by `{status_field}`",as_dict=True)
    return [{"value":r.value,"indicator":"Blue","label":r.label or "Not Set","datatype":"Int"} for r in rows]
