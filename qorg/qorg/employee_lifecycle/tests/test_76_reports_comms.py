import ast,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
def test_two_focused_reports_follow_application_pattern():
 for slug,name,ref in [('training_overview','Training Overview','Training Event'),('evaluation_overview','Evaluation Overview','Appraisal')]:
  root=ROOT/f'qorg/qorg/report/{slug}'
  meta=json.loads((root/f'{slug}.json').read_text())
  assert meta['name']==name and meta['report_type']=='Script Report' and meta['is_standard']=='Yes' and meta['ref_doctype']==ref
  js=(root/f'{slug}.js').read_text();py=(root/f'{slug}.py').read_text()
  assert 'Reset Filters' in js and 'indicator-pill' in js and 'report-summary' in js
  assert 'finalize_report_result' in py and 'report_summary' not in py
  assert "'Exceptions'" in py and "'view'" in js
def test_reports_are_permission_scoped_and_not_excessive():
 for slug in ('training_overview','evaluation_overview'):
  meta=json.loads((ROOT/f'qorg/qorg/report/{slug}/{slug}.json').read_text())
  assert {x['role'] for x in meta['roles']}=={'HR User','HR Manager','System Manager'}
def test_bilingual_managed_templates_and_notifications():
 source=(ROOT/'qorg/qorg/employee_lifecycle/comms.py').read_text();ast.parse(source)
 for token in ('QORG-LEARNING-COMM-v1.0','QOrg Training Action','QOrg Training Result','QOrg Evaluation Assignment','QOrg Appraisal Result','عرض السجل | View Record','direction:rtl','direction:ltr'):
  assert token in source
 assert 'reference_doctype=doctype' in source and 'reference_name=name' in source
 assert "doc.save(ignore_permissions=True)" in source
def test_preview_send_buttons_match_existing_interaction_pattern():
 js=(ROOT/'qorg/public/js/learning_comms.js').read_text()
 for token in ('Preview Email','Recipients','CC','Subject','Message','primary_action_label','Email queued'):
  assert token in js
 for dt in ('Training Follow-up','Training Result','Evaluation Assignment','Appraisal'):
  assert dt in js
def test_hooks_register_assets_and_setup():
 hooks=(ROOT/'qorg/hooks.py').read_text();ast.parse(hooks)
 assert 'comms.provision_communications' in hooks
 assert hooks.count('public/js/learning_comms.js')==4
