import frappe
from frappe import _
from frappe.utils import flt, cint

def _validate_total(rows, fieldname, label):
    rows=rows or []
    if not rows:return
    total=flt(sum(flt(r.get(fieldname)) for r in rows),2)
    diff=flt(100-total,2)
    if abs(diff)>0.01:
        action=_("add") if diff>0 else _("remove")
        frappe.throw(_("{0} must total exactly 100%. Current total: {1}%. Please {2} {3}%.").format(label,total,action,abs(diff)))

def validate_designation(doc,method=None):
    rows=doc.get("qorg_interview_criteria") or []
    _validate_total(rows,"default_weight",_("Default Interview Criteria weights"))
    seq=set()
    for row in rows:
        if cint(row.sequence) in seq:frappe.throw(_("Default Interview Criteria sequence must be unique. Duplicate: {0}.").format(row.sequence))
        seq.add(cint(row.sequence))
        if not (row.question_task or "").strip():frappe.throw(_("Question / Task is required in every default criterion."))
        if flt(row.passing_score)<0 or flt(row.passing_score)>100:frappe.throw(_("Criterion passing score must be between 0 and 100%."))

def validate_interview_type(doc,method=None):
    _validate_total(doc.get("qorg_evaluation_criteria") or [],"weight",_("Interview Type evaluation criterion weights"))

def validate_job_opening(doc,method=None):
    sw=flt(doc.get("qorg_screening_weight"));aw=flt(doc.get("qorg_assessment_weight"))
    if abs(sw+aw-100)>0.01:frappe.throw(_("Screening and Assessment weights must total exactly 100%. Current total: {0}%.").format(flt(sw+aw,2)))
    _validate_total(doc.get("qorg_assessment_plan") or [],"weight",_("Assessment stage weights"))

def validate_feedback(doc,method=None):
    _validate_total(doc.get("qorg_criterion_scores") or [],"weight",_("Interview Feedback criterion weights"))
