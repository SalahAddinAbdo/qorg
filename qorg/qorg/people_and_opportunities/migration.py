from __future__ import annotations
import frappe
from qorg.qorg.people_and_opportunities.services.people import get_or_create_external_person
FIELD_CANDIDATES={"full_name":["employee_name","full_name"],"name_in_arabic":["arabic_name","name_in_arabic"],"primary_email":["email","email_id","personal_email"],"mobile_no":["mobile_no","cell_number","phone"],"professional_title":["job_title","profession","designation"],"professional_summary":["professional_summary","summary","about"]}
def _first(doc,names):
    for name in names:
        if doc.meta.has_field(name) and doc.get(name): return doc.get(name)
    return None
@frappe.whitelist()
def migrate_hr_database(dry_run: int = 1, limit: int = 0):
    if frappe.session.user != "Administrator": frappe.throw("Administrator is required.", frappe.PermissionError)
    if not frappe.db.exists("DocType","HR Database"): return {"available":False,"message":"HR Database is not installed."}
    names=frappe.get_all("HR Database",pluck="name",limit=int(limit or 0)); result={"available":True,"scanned":len(names),"would_create":0,"linked_existing":0,"created":0,"errors":[]}
    for name in names:
        try:
            old=frappe.get_doc("HR Database",name); values={target:_first(old,candidates) for target,candidates in FIELD_CANDIDATES.items()}; values["full_name"]=values.get("full_name") or name
            existing=None
            if values.get("primary_email"): existing=frappe.db.get_value("External Person",{"primary_email":values["primary_email"].strip().lower()},"name")
            if existing: result["linked_existing"]+=1; continue
            result["would_create"]+=1
            if not int(dry_run):
                person=get_or_create_external_person(values,"Migration","HR Database",name); result["created"]+=1
        except Exception as exc: result["errors"].append({"source":name,"error":str(exc)})
    return result

