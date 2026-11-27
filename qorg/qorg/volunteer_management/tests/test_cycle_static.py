import ast,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]

def test_cycle_python_syntax():
 for p in (ROOT/'qorg/qorg/volunteer_management').rglob('*.py'):ast.parse(p.read_text())
 ast.parse((ROOT/'qorg/hooks.py').read_text())

def test_participation_hooks_are_registered_once():
 hooks=(ROOT/'qorg/hooks.py').read_text()
 required_handlers=(
  'qorg.qorg.volunteer_management.events.validate_external_opportunity',
  'qorg.qorg.volunteer_management.cycle_integrity.validate_participation_record',
  'qorg.qorg.volunteer_management.integrity.prevent_operational_delete',
  'qorg.qorg.volunteer_management.provisioning.provision_volunteer_management',
 )
 for handler in required_handlers:
  assert handler in hooks,handler
 assert hooks.count('qorg.qorg.volunteer_management.events.validate_external_opportunity')==1
 assert hooks.count('def _qorg_participation_add_event')<=1

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
 assert 'validate_weekly_service_hours' in services
 assert 'service_date BETWEEN' in services
 assert 'Existing hours for this week' in services
 assert 'Resulting total' in services
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


def test_recalculations_run_after_delete_and_verification_is_persisted():
 assessment=(ROOT/'qorg/qorg/doctype/participation_assessment/participation_assessment.py').read_text()
 service_log=(ROOT/'qorg/qorg/doctype/participation_service_log/participation_service_log.py').read_text()
 assert 'def after_delete' in assessment
 assert 'def on_trash' not in assessment
 assert 'def after_delete' in service_log
 assert 'def on_trash' not in service_log
 validate_block=service_log.split('def on_update',1)[0]
 assert 'self.verified_by = frappe.session.user' in validate_block
 assert 'self.verified_on = now_datetime()' in validate_block


def test_runtime_audit_covers_full_participation_configuration():
 source=(ROOT/'qorg/qorg/volunteer_management/acceptance.py').read_text()
 for marker in (
  'qorg_participation_max_weekly_hours',
  'qorg_participation_require_evidence',
  'qorg_participation_require_decision_rationale',
  'Participation Clearance Item',
  'participation-application',
  'Legacy DocType still exists',
  'EXPECTED_CONTROLLER_METHODS',
 ):
  assert marker in source,marker


def test_business_limits_are_configuration_driven():
 services=(ROOT/'qorg/qorg/volunteer_management/services.py').read_text()
 custom_fields=json.loads((ROOT/'qorg/qorg/volunteer_management/data/custom_fields.json').read_text())
 managed={row.get('fieldname') for row in custom_fields if row.get('dt')=='HR Settings'}
 for fieldname in (
  'qorg_participation_max_daily_hours',
  'qorg_participation_max_weekly_hours',
  'qorg_participation_require_decision_rationale',
 ):
  assert fieldname in managed
  assert fieldname in services
 assert 'or 8' not in services
 assert 'or 40' not in services
 assert 'or 60' not in services
 assert 'require_decision_rationale": 1' not in services
 assert 'else 1' not in services
 assert 'Set Maximum Hours per Day in HR Settings' in services
 assert 'Set Maximum Hours per Week in HR Settings' in services
 assert 'Set the Passing Score for assessment stage' in services


def test_hr_settings_layout_is_isolated_and_balanced():
 custom_fields=json.loads((ROOT/'qorg/qorg/volunteer_management/data/custom_fields.json').read_text())
 layouts=json.loads((ROOT/'qorg/qorg/volunteer_management/data/form_layouts.json').read_text())
 fields={row.get('fieldname'):row for row in custom_fields if row.get('dt')=='HR Settings'}
 ordered=layouts['HR Settings']
 assert ordered[0]=='qorg_participation_management_tab'
 assert fields['qorg_participation_management_tab']['fieldtype']=='Tab Break'
 for section in (
  'qorg_participation_general_section',
  'qorg_participation_hours_section',
  'qorg_participation_intern_section',
 ):
  assert fields[section]['fieldtype']=='Section Break'
 for column in (
  'qorg_participation_general_cb',
  'qorg_participation_general_cb_2',
  'qorg_participation_hours_cb',
  'qorg_participation_hours_cb_2',
  'qorg_participation_intern_cb',
 ):
  assert fields[column]['fieldtype']=='Column Break'
  assert column in ordered
 assert len(ordered)==len(set(ordered))


def test_all_exposed_participation_settings_have_runtime_effects():
 services=(ROOT/'qorg/qorg/volunteer_management/services.py').read_text()
 custom_fields=json.loads((ROOT/'qorg/qorg/volunteer_management/data/custom_fields.json').read_text())
 setting_fields=[
  row['fieldname'] for row in custom_fields
  if row.get('dt')=='HR Settings'
  and row.get('fieldtype') not in ('Tab Break','Section Break','Column Break')
 ]
 for fieldname in setting_fields:
  assert fieldname in services,fieldname
 for function_name in (
  'validate_service_log_verifier',
  'validate_expected_hours',
  'validate_weekly_service_hours',
 ):
  assert f'def {function_name}' in services
 assert 'doc.external_person = engagement.external_person' in services
 assert 'doc.supervisor = engagement.supervisor' in services


def test_layout_reconciliation_preserves_standard_field_order():
 source=(ROOT/'qorg/qorg/volunteer_management/layout.py').read_text()
 assert 'def _layout_anchor' in source
 assert 'field.fieldname not in managed_fields' in source
 assert 'idx=900' not in source.replace(' ', '')
 assert 'update_modified=False' in source
