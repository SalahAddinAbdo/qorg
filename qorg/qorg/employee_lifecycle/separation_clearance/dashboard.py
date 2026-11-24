import frappe
def get_data(data=None):
 r=data or {};items=[x for x in ("Exit Interview","Full and Final Statement","Contract","Asset Custody","Stock Handover","Employee Advance","Expense Claim","Salary Slip","Employee Document Record") if frappe.db.exists("DocType",x)]
 labels={x.get("label") for x in r.get("transactions",[])}
 if items and "Clearance and Closeout" not in labels:r.setdefault("transactions",[]).append({"label":"Clearance and Closeout","items":items})
 return r
