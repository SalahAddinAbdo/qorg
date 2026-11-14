import ast,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]

def test_python_syntax():
 for p in [ROOT/'qorg/qorg/recruitment_extensions/employee_cycle_integrity.py',ROOT/'qorg/qorg/procurement_contracting/complaint_permissions.py',ROOT/'qorg/qorg/procurement_contracting/doctype_validators.py',ROOT/'qorg/hooks.py']:ast.parse(p.read_text())

def test_latest_cumulative_hooks_and_cycle4_are_present():
 hooks=(ROOT/'qorg/hooks.py').read_text()
 for marker in ('Project cycle integrity validation.','People, opportunities and recruitment cycle integrity.','Volunteer, internship and participation cycle integrity.','Employee lifecycle, separation and complaint confidentiality controls.'):
  assert marker in hooks
 assert 'Procurement Complaint' in hooks
 assert 'prevent_incomplete_employee_exit' in hooks

def test_employee_exit_checks_custody_and_handover():
 source=(ROOT/'qorg/qorg/recruitment_extensions/employee_cycle_integrity.py').read_text()
 assert 'Asset Custody' in source
 assert 'Stock Handover' in source
 assert 'Pending Handover' in source
 assert 'Discrepancy Review' in source

def test_complaint_decision_and_confidentiality_controls():
 validator=(ROOT/'qorg/qorg/procurement_contracting/doctype_validators.py').read_text()
 permissions=(ROOT/'qorg/qorg/procurement_contracting/complaint_permissions.py').read_text()
 for marker in ('Assigned To is required','Investigation Findings are required','Corrective Action is required','complaint record owner'):
  assert marker in validator
 assert 'Procurement Manager' in permissions
 assert 'Procurement Complaint Reviewer' not in permissions
 assert 'assigned_to' in permissions

def test_cycle4_doctype_dependencies_resolve():
 for slug in ('work_commencement_notice','asset_custody','asset_incident','project_risk','project_compliance_deliverable','procurement_complaint'):
  p=ROOT/'qorg/qorg/doctype'/slug/f'{slug}.json';d=json.loads(p.read_text());names={x.get('fieldname') for x in d.get('fields',[])}|{'docstatus','workflow_state'}
  for f in d.get('fields',[]):
   for prop in ('depends_on','mandatory_depends_on','read_only_depends_on'):
    for ref in re.findall(r'doc\.([A-Za-z0-9_]+)',str(f.get(prop) or '')):
     assert ref in names,(p,f.get('fieldname'),prop,ref)


def test_internal_custody_signatures_are_removed():
 d=json.loads((ROOT/'qorg/qorg/doctype/asset_custody/asset_custody.json').read_text())
 names={x['fieldname'] for x in d['fields']}
 assert not ({'custodian_signature','handover_signature','return_signature'} & names)

def test_complaint_acknowledgement_is_provisioned_and_actionable():
 communication=(ROOT/'qorg/qorg/procurement_contracting/communications.py').read_text()
 hooks=(ROOT/'qorg/hooks.py').read_text()
 action=(ROOT/'qorg/public/js/procurement_complaint.js').read_text()
 assert '"Procurement Complaint Acknowledgement": ("Procurement Complaint"' in communication
 assert 'procurement_complaint.js' in hooks
 assert 'preview_template' in action
 assert 'send_template' in action
 assert 'Procurement Complaint Acknowledgement' in action
