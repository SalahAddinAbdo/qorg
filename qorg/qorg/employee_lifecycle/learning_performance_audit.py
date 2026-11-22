from __future__ import annotations
import json
from pathlib import Path
import frappe
from frappe import _
STANDARD_CAPABILITIES={"training":{"Training Program":"Reusable programme definition","Training Event":"Scheduled delivery instance","Training Event Employee":"Participants and attendance","Training Result":"Event results","Training Result Employee":"Employee result","Training Feedback":"Participant feedback","Employee Training":"Employee history"},"performance":{"Appraisal Template":"Reusable appraisal structure","Appraisal Cycle":"Period and population","Appraisal":"Employee appraisal","Employee Performance Feedback":"Reviewer response","Goal":"Employee goals","KRA":"Key result areas"},"skills":{"Employee Skill Map":"Employee skill inventory","Employee Skill":"Skill rows","Skill Assessment":"Skill assessment","Designation Skill":"Designation requirements","Expected Skill Set":"Expected skill profile"}}
GAP_CAPABILITIES={"Training Need Request":"Training demand and approval","Training Need Participant":"Named participants","Employee Development Action":"Appraisal and skill-gap action","Training Assessment":"Auditable assessment attempts","Training Follow-up":"Post-training effectiveness","Employee Evaluation Type":"Reusable evaluation policy","Evaluation Source Weight":"Source and weight policy","Employee Evaluation Assignment":"Reviewer assignment and anonymity","Evaluation Source Result":"Protected calculation snapshot","Performance Rating Scale":"Configurable score bands"}
FIELD_EXPECTATIONS={"Training Event Employee":("employee","employee_name","department","attendance","status"),"Training Result Employee":("employee","employee_name"),"Appraisal Cycle":("company","start_date","end_date"),"Appraisal":("employee","employee_name"),"Employee Performance Feedback":("employee",),"Employee Skill Map":("employee","employee_skills")}
def run_audit(write_file=False,file_path=None):
 report={"apps":frappe.get_installed_apps(_ensure_on_bench=True),"standard":{},"gaps":{},"conflicts":[],"recommendations":[]}
 for area,doctypes in STANDARD_CAPABILITIES.items():report["standard"][area]={name:_inspect_doctype(name,purpose) for name,purpose in doctypes.items()}
 for name,purpose in GAP_CAPABILITIES.items():report["gaps"][name]=_inspect_doctype(name,purpose)
 report["conflicts"]=_detect_conflicts(report);report["recommendations"]=_recommendations(report);report["summary"]=_summary(report)
 if write_file:
  path=Path(file_path or frappe.get_site_path("private","files","learning_performance_audit.json"));path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(report,indent=2,ensure_ascii=False,default=str)+"\n");report["output_file"]=str(path)
 return report
def _inspect_doctype(name,purpose):
 exists=bool(frappe.db.exists("DocType",name));result={"exists":exists,"purpose":purpose,"module":None,"custom":None,"fields":[],"permissions":[]}
 if not exists:return result
 meta=frappe.get_meta(name);result.update({"module":meta.module,"custom":bool(meta.custom),"is_submittable":bool(meta.is_submittable),"track_changes":bool(meta.track_changes),"fields":[f.fieldname for f in meta.fields],"permissions":sorted({p.role for p in meta.permissions if p.role}),"missing_expected_fields":[f for f in FIELD_EXPECTATIONS.get(name,()) if not meta.has_field(f)]});return result
def _detect_conflicts(report):
 conflicts=[]
 for area in report["standard"].values():
  for name,row in area.items():
   if row["exists"] and row["custom"]:conflicts.append(_("Standard capability {0} is a Custom DocType; review ownership.").format(name))
 for name,row in report["gaps"].items():
  if row["exists"] and row["module"] not in {"QOrg","HR"}:conflicts.append(_("Gap DocType {0} already exists in module {1}; do not duplicate it.").format(name,row["module"]))
 return conflicts
def _recommendations(report):
 rows=[]
 for area,doctypes in report["standard"].items():
  missing=[name for name,row in doctypes.items() if not row["exists"]]
  if missing:rows.append({"area":area,"action":"verify_version_or_fallback","doctypes":missing})
 for name,row in report["gaps"].items():rows.append({"doctype":name,"action":"reuse_and_harden" if row["exists"] else "create_only_if_approved_gap","reason":row["purpose"]})
 rows += [{"action":"do_not_replace_standard_field_order","scope":["Training Event","Appraisal","Appraisal Cycle","Employee Performance Feedback"]},{"action":"centralize_domain_logic","modules":["learning.py","performance.py","development_history.py"]},{"action":"preserve_authoritative_ownership","owners":{"training_delivery":"Training Event","appraisal":"Appraisal","feedback":"Employee Performance Feedback","skills":"Employee Skill Map"}}]
 return rows
def _summary(report):
 standard=[r for area in report["standard"].values() for r in area.values()];gaps=list(report["gaps"].values());return {"standard_expected":len(standard),"standard_found":sum(r["exists"] for r in standard),"approved_gap_models_found":sum(r["exists"] for r in gaps),"conflicts":len(report["conflicts"])}
