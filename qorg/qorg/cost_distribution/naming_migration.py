from __future__ import annotations
import frappe

RENAMES=(("Service and Allowance Accrual","Service Allowance Accrual"),("Service and Allowance Accrual Line","Service Allowance Line"),("Cost Distribution Profile Target","Cost Distribution Target"),("Cost Distribution Transaction Type","Cost Distribution Scope"),("Planned versus Actual Distribution","Planned vs Actual Cost"))

def rename_legacy_records():
    for old,new in RENAMES:
        if frappe.db.exists("DocType",old) and not frappe.db.exists("DocType",new):
            frappe.rename_doc("DocType",old,new,force=True)
        if frappe.db.exists("Report",old) and not frappe.db.exists("Report",new):
            frappe.rename_doc("Report",old,new,force=True)
