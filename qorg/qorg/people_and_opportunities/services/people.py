from __future__ import annotations
import re, frappe
from frappe.utils import now
from qorg.qorg.people_and_opportunities.settings import settings
def normalize_email(value): return (value or "").strip().lower()
def normalize_mobile(value): return re.sub(r"[^0-9+]", "", (value or "").strip())
def validate_external_person(doc):
    doc.primary_email=normalize_email(doc.primary_email); doc.secondary_email=normalize_email(doc.secondary_email); doc.mobile_no=normalize_mobile(doc.mobile_no); doc.alternative_mobile_no=normalize_mobile(doc.alternative_mobile_no)
    if not doc.full_name: frappe.throw("Full Name is required.")
    config=settings()
    if config.match_by_official_id and doc.identification_number and doc.identification_type:
        duplicate=frappe.db.get_value("External Person",{"identification_type":doc.identification_type,"identification_number":doc.identification_number,"identification_country":doc.identification_country or "","name":("!=",doc.name or "")},"name")
        if duplicate: frappe.throw(f"The same official identity is already linked to {duplicate}.")
    matching=[]
    if config.match_by_email: matching.append("primary_email")
    if config.match_by_mobile: matching.append("mobile_no")
    for field in matching:
        value=doc.get(field)
        if value:
            duplicate=frappe.db.get_value("External Person",{field:value,"name":("!=",doc.name or ""),"person_status":("!=","Merged")},"name")
            if duplicate: frappe.throw(f"{field.replace('_',' ').title()} is already linked to {duplicate}.")
def update_profile_metrics(doc):
    required=[doc.full_name,doc.primary_email or doc.mobile_no,doc.professional_title,doc.professional_summary,doc.education,doc.experience,doc.skills]
    doc.profile_completion=round(sum(bool(x) for x in required)*100/len(required),2)
    total=0.0
    for row in doc.experience or []:
        if row.from_date:
            end=frappe.utils.getdate(row.to_date or frappe.utils.today()); start=frappe.utils.getdate(row.from_date)
            if end>=start: total += (end-start).days/365.25
    doc.years_of_experience=round(total,2); doc.last_profile_update=now()
def get_or_create_external_person(data,source=None,reference_doctype=None,reference_name=None):
    email=normalize_email(data.get("primary_email")); mobile=normalize_mobile(data.get("mobile_no"))
    name=None
    if email:name=frappe.db.get_value("External Person",{"primary_email":email,"person_status":("!=","Merged")},"name")
    if not name and mobile:name=frappe.db.get_value("External Person",{"mobile_no":mobile,"person_status":("!=","Merged")},"name")
    if name:return frappe.get_doc("External Person",name)
    values={"doctype":"External Person","full_name":data.get("full_name"),"primary_email":email,"mobile_no":mobile,"source":source or "Manual Entry","source_reference_doctype":reference_doctype,"source_reference_name":reference_name}
    for fieldname in ("name_in_arabic","professional_title","professional_summary","career_objective"):
        if data.get(fieldname): values[fieldname]=data.get(fieldname)
    doc=frappe.get_doc(values); doc.insert(ignore_permissions=True); return doc
