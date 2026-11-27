from __future__ import annotations
import frappe

def prevent_master_delete(doc, method=None):
    checks={
        "External Opportunity Type":[("External Opportunity","opportunity_type"),],
        "Person Qualification":[("External Person Education","qualification"),],
        "Volunteer Category":[],
    }
    for target,field in checks.get(doc.doctype,[]):
        if frappe.db.exists(target,{field:doc.name}):
            frappe.throw(f"Cannot delete {doc.doctype} because it is used in {target}.")

def prevent_operational_delete(doc, method=None):
    links={
        "External Person":[("Job Applicant","qorg_external_person"),("Participation Application","external_person"),("Participation Engagement","external_person")],
        "External Opportunity":[("Participation Application","opportunity"),("Participation Engagement","opportunity")],
    }
    for target,field in links.get(doc.doctype,[]):
        if frappe.db.exists("DocType",target) and frappe.db.exists(target,{field:doc.name}):
            frappe.throw(f"Cannot delete {doc.doctype} because linked {target} records exist.")
