import ast,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]

def test_cycle_python_syntax():
 for p in (ROOT/'qorg/qorg/volunteer_management').rglob('*.py'):ast.parse(p.read_text())
 ast.parse((ROOT/'qorg/hooks.py').read_text())

def test_latest_shared_hooks_are_preserved_and_cycle_added_once():
 hooks=(ROOT/'qorg/hooks.py').read_text()
 for marker in ('Project cycle integrity validation.','People, opportunities and recruitment cycle integrity.','Volunteer, internship and participation cycle integrity.'):
  assert marker in hooks
 assert hooks.count('def _qorg_participation_add_event')==1
 for handler in ('validate_participation_record','validate_volunteer_record'):
  assert hooks.count(handler)>=1

def test_weights_and_zero_scores_are_correct():
 services=(ROOT/'qorg/qorg/volunteer_management/services.py').read_text()
 evaluation=(ROOT/'qorg/qorg/doctype/participation_evaluation/participation_evaluation.py').read_text()
 assert 'weights must total 100%' in services
 assert 'x>0' not in evaluation
 assert 'sum(values)/len(values)' in evaluation

def test_allowance_and_service_controls_exist():
 allowance=(ROOT/'qorg/qorg/doctype/participation_allowance/participation_allowance.py').read_text()
 services=(ROOT/'qorg/qorg/volunteer_management/services.py').read_text()
 assert 'cannot be negative' in allowance
 assert 'Approved Amount exceeds Amount' in allowance
 assert 'maximum_hours_per_day' in services
 assert 'maximum_hours_per_week' in services
 assert 'require_service_log_evidence' in services

def test_notifications_are_meta_and_company_identity_aware():
 source=(ROOT/'qorg/qorg/volunteer_management/notifications.py').read_text()
 assert 'def _template_body' in source
 assert 'meta.has_field("response_html")' in source
 assert 'custom_print_primary_color' in source
 assert 'custom_print_accent_color' in source
 assert 'reference_doctype=reference_doctype' in source
 assert 'reference_name=reference_name' in source

def test_participation_dependencies_resolve():
 for p in (ROOT/'qorg/qorg/doctype').glob('participation_*/*.json'):
  d=json.loads(p.read_text());names={x.get('fieldname') for x in d.get('fields',[])}|{'docstatus','workflow_state'}
  for field in d.get('fields',[]):
   for prop in ('depends_on','mandatory_depends_on','read_only_depends_on'):
    for ref in re.findall(r'doc\.([A-Za-z0-9_]+)',str(field.get(prop) or '')):
     assert ref in names,(p,field.get('fieldname'),prop,ref)

def test_all_managed_templates_have_form_actions():
 hooks=(ROOT/'qorg/hooks.py').read_text()
 source=(ROOT/'qorg/public/js/participation_communications.js').read_text()
 assert 'participation_communications.js' in hooks
 for doctype in ('Participation Application','Participation Engagement','Participation Service Log','Participation Certificate'):
  assert f'"{doctype}"' in source
 templates=[]
 for p in (ROOT/'qorg/qorg/volunteer_management/data/email_templates').glob('*.json'):
  templates.append(json.loads(p.read_text())['name'])
 for template in templates:
  assert template in source,template
 assert 'preview_notification' in source
 assert 'send_notification' in source
 assert 'Preview or Send Communication' in source
