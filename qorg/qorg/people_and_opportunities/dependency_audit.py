from __future__ import annotations
import json
from pathlib import Path
import frappe
OWNED={"External Person","External Person Education","External Person Experience","External Person Training","External Person Language","External Person Skill","External Person Volunteer Experience","External Person Reference","External Opportunity","Opportunity Location","Opportunity Requirement","Opportunity Screening Question","Opportunity Screening Answer","Volunteer Application","Volunteer Profile","Volunteer Engagement","External Opportunity Type","Person Qualification","Volunteer Category"}
@frappe.whitelist()
def audit_dependencies():
    if frappe.session.user!="Administrator": frappe.throw("Administrator is required.",frappe.PermissionError)
    missing=[];checked=[]
    for dt in sorted(OWNED):
        if not frappe.db.exists("DocType",dt): missing.append({"source":"Package","reference":dt})
        else:
            meta=frappe.get_meta(dt)
            for field in meta.fields:
                if field.fieldtype in {"Link","Table"} and field.options:
                    checked.append({"source":dt,"field":field.fieldname,"reference":field.options})
                    if not frappe.db.exists("DocType",field.options): missing.append({"source":dt,"field":field.fieldname,"reference":field.options})
    return {"checked":checked,"missing":missing,"ok":not missing}
