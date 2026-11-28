from __future__ import annotations
import frappe
REQUIRED_DOCTYPES=("Accountability Case","Investigation Case","Corrective Action","Enterprise Risk","Compliance Obligation","Assurance Finding","Accountability Settings")
REQUIRED_REPORTS=("Accountability Case Resolution","Enterprise Risk Register","Compliance Status","Assurance Findings","Corrective Action Tracking","Complaint Resolution")
REQUIRED_TEMPLATES=("Accountability - Case Acknowledgement - Bilingual","Accountability - Case Status Update - Bilingual","Accountability - Case Response - Bilingual","Accountability - Case Closure - Bilingual")
def audit_runtime_configuration():
 missing=[]
 for name in REQUIRED_DOCTYPES:
  if not frappe.db.exists('DocType',name):missing.append(f'DocType:{name}')
 for name in REQUIRED_REPORTS:
  if not frappe.db.exists('Report',name):missing.append(f'Report:{name}')
 for name in REQUIRED_TEMPLATES:
  if not frappe.db.exists('Email Template',name):missing.append(f'Email Template:{name}')
 settings=frappe.get_single('Accountability Settings') if not missing else None
 return {'ok':not missing,'missing':missing,'public_intake_enabled':bool(settings and settings.enable_public_intake),'public_tracking_enabled':bool(settings and settings.enable_public_tracking)}
def audit_deep_runtime_configuration():
 base=audit_runtime_configuration(); migration=frappe.get_attr('qorg.qorg.governance_accountability.migration.audit_procurement_migration')() if frappe.db.exists('DocType','Procurement Complaint') else {'ok':True,'skipped':True}
 base['procurement_migration']=migration;base['ok']=bool(base['ok'] and migration.get('ok'));return base
