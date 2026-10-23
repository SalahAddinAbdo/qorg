import frappe
from frappe import _
from . import services

@frappe.whitelist(methods=["POST"])
def import_designation_criteria(interview_type, mode="append"):
    doc=frappe.get_doc("Interview Type",interview_type); doc.check_permission("write")
    designation=doc.get("designation")
    if not designation: frappe.throw(_("Designation is required."))
    source=frappe.get_all("Designation Interview Criterion",filters={"parent":designation,"parenttype":"Designation","parentfield":"qorg_interview_criteria"},fields=["name","sequence","competency_area","question_task","applicable_assessment_type","assessment_method","default_weight","passing_score","is_mandatory","low_score_anchor","mid_score_anchor","high_score_anchor","instructions"],order_by="sequence asc")
    atype=doc.get("qorg_assessment_type")
    source=[r for r in source if r.applicable_assessment_type in (None,"","All",atype)]
    if mode=="replace": doc.set("qorg_evaluation_criteria",[])
    existing={(r.competency_area or "",r.question_task or "",r.assessment_method or "") for r in doc.get("qorg_evaluation_criteria") or []}
    for r in source:
        key=(r.competency_area or "",r.question_task or "",r.assessment_method or "")
        if key in existing: continue
        doc.append("qorg_evaluation_criteria",{"source_designation_criterion":r.name,"sequence":r.sequence,"competency_area":r.competency_area,"question_task":r.question_task,"assessment_method":r.assessment_method,"weight":r.default_weight,"passing_score":r.passing_score,"is_mandatory":r.is_mandatory,"low_score_anchor":r.low_score_anchor,"mid_score_anchor":r.mid_score_anchor,"high_score_anchor":r.high_score_anchor,"instructions":r.instructions})
    services.validate_interview_type(doc); doc.save(); return doc.name
