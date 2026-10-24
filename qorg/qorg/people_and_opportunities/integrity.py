from __future__ import annotations
import frappe

def prevent_master_delete(doc, method=None):
    checks={
        "External Opportunity Type":[("External Opportunity","opportunity_type"),],
        "Person Qualification":[("External Person Education","qualification"),],
        "Volunteer Category":[("Volunteer Profile","volunteer_category"),("Volunteer Engagement","volunteer_category")],
    }
    for target,field in checks.get(doc.doctype,[]):
        if frappe.db.exists(target,{field:doc.name}):
            frappe.throw(f"Cannot delete {doc.doctype} because it is used in {target}.")

def prevent_operational_delete(doc, method=None):
    links={
        "External Person":[("Job Applicant","qorg_external_person"),("Volunteer Application","external_person"),("Volunteer Profile","external_person")],
        "External Opportunity":[("Volunteer Application","external_opportunity"),("Volunteer Engagement","external_opportunity")],
        "Volunteer Profile":[("Volunteer Engagement","volunteer_profile")],
    }
    for target,field in links.get(doc.doctype,[]):
        if frappe.db.exists("DocType",target) and frappe.db.exists(target,{field:doc.name}):
            frappe.throw(f"Cannot delete {doc.doctype} because linked {target} records exist.")
