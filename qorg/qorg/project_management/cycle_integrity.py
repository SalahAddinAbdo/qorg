from __future__ import annotations
import frappe
from frappe import _
from frappe.utils import getdate

LINKS={
 "Project Result":{"parent_result":"Project Result"},
 "Project Indicator":{"result":"Project Result","project_result":"Project Result"},
 "Indicator Target Plan":{"indicator":"Project Indicator"},
 "Project Workplan Activity":{"result":"Project Result","project_result":"Project Result","indicator":"Project Indicator"},
 "Project Progress Update":{"activity":"Project Workplan Activity","workplan_activity":"Project Workplan Activity","indicator":"Project Indicator"},
}
DATE_PAIRS=(("start_date","end_date"),("planned_start_date","planned_end_date"),("reporting_period_start","reporting_period_end"))

def _project_of(doctype,name):
 return frappe.db.get_value(doctype,name,"project") if name and frappe.db.exists(doctype,name) else None

def validate_project_cycle_links(doc,method=None):
 project=doc.get("project")
 if not project:return
 for fieldname,target in LINKS.get(doc.doctype,{}).items():
  if not doc.meta.has_field(fieldname) or not doc.get(fieldname):continue
  linked_project=_project_of(target,doc.get(fieldname))
  if linked_project and linked_project!=project:
   frappe.throw(_("{0} must belong to Project {1}.").format(doc.meta.get_label(fieldname),project))
 for start_field,end_field in DATE_PAIRS:
  if doc.meta.has_field(start_field) and doc.meta.has_field(end_field) and doc.get(start_field) and doc.get(end_field) and getdate(doc.get(end_field))<getdate(doc.get(start_field)):
   frappe.throw(_("{0} cannot be before {1}.").format(doc.meta.get_label(end_field),doc.meta.get_label(start_field)))
 if doc.doctype=="Project Result" and doc.parent_result:
  parent=frappe.db.get_value("Project Result",doc.parent_result,["project","result_level"],as_dict=True)
  allowed={"Outcome":{"Impact / Goal"},"Output":{"Outcome"}}
  if parent and parent.result_level not in allowed.get(doc.result_level,set()):
   frappe.throw(_("Invalid result hierarchy: {0} cannot be under {1}.").format(doc.result_level,parent.result_level))
