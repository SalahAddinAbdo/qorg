import ast,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
def read(p):return (ROOT/p).read_text()
def load(p):return json.loads(read(p))
def test_every_managed_json_field_order_is_exact_and_unique():
 for p in (ROOT/'qorg/qorg/doctype').glob('*/*.json'):
  d=json.loads(p.read_text())
  if d.get('module')!='QOrg':continue
  names=[x['fieldname'] for x in d.get('fields',[])]
  assert names==d.get('field_order',[]),p
  assert len(names)==len(set(names)),p
def test_child_grids_are_concise_and_row_dialogs_have_layout():
 for slug in ('accountability_follow_up','accountability_referral','accountability_response_log','investigation_team_member','investigation_interview','investigation_evidence','investigation_finding','corrective_action_update','risk_assessment_entry','risk_treatment_action','compliance_review_entry'):
  d=load(f'qorg/qorg/doctype/{slug}/{slug}.json');visible=[x for x in d['fields'] if x.get('in_list_view')]
  assert 1<=len(visible)<=8 and sum(int(x.get('columns',0)) for x in visible)<=10,slug
  assert any(x['fieldtype']=='Section Break' for x in d['fields']),slug
def test_text_editors_and_tables_are_not_in_split_column_sections():
 for slug in ('accountability_case','investigation_case','corrective_action','enterprise_risk','compliance_obligation','assurance_finding'):
  d=load(f'qorg/qorg/doctype/{slug}/{slug}.json');fs=d['fields']
  for i,f in enumerate(fs):
   if f['fieldtype'] not in ('Text Editor','Table'):continue
   boundary=next((x for x in fs[i+1:] if x['fieldtype'] in ('Column Break','Section Break','Tab Break')),None)
   assert not boundary or boundary['fieldtype']!='Column Break',(slug,f['fieldname'])
def test_settings_are_validated_and_consumed():
 settings=read('qorg/qorg/doctype/accountability_settings/accountability_settings.py');validation=read('qorg/qorg/governance_accountability/validations.py');scheduled=read('qorg/qorg/governance_accountability/scheduled_tasks.py')
 for name in ('complex_response_days','captcha_verifier_method','intake_rate_limit_per_hour'):assert name in settings
 for name in ('default_triage_days','complex_response_days','update_frequency_days'):assert name in validation
 assert 'critical_escalation_role' in scheduled
def test_reports_use_permission_aware_get_list_summaries_charts_views_and_dates():
 for slug in ('accountability_case_resolution','enterprise_risk_register','compliance_status','assurance_findings','corrective_action_tracking'):
  py=read(f'qorg/qorg/report/{slug}/{slug}.py');js=read(f'qorg/qorg/report/{slug}/{slug}.js')
  assert 'frappe.get_list' in py and 'summary(' in py and 'chart(' in py and 'view_columns' in py
  assert 'from_date' in js and 'to_date' in js and 'Executive' in js and 'qorg-sticky-report' in js
def test_dashboard_workspace_and_metrics_are_integrated():
 hooks=read('qorg/hooks.py');prov=read('qorg/qorg/governance_accountability/provisioning.py');ws=load('qorg/qorg/workspace/governance_accountability/governance_accountability.json')
 assert 'Procurement Process' in hooks and 'Accountability Case' in hooks and 'Enterprise Risk' in hooks
 assert '_provision_workspace_metrics(result)' in prov and len(ws['number_cards'])==5
def test_guest_tracking_is_post_only_and_verifier_configurable():
 portal=read('qorg/qorg/governance_accountability/portal.py');sec=read('qorg/qorg/governance_accountability/security.py')
 assert portal.count('allow_guest=True,methods=["POST"]')==2
 assert 'captcha_verifier_method' in sec and 'frappe.get_attr' in sec
def test_python_sources_parse():
 for p in (ROOT/'qorg').rglob('*.py'):ast.parse(p.read_text())
def test_workspace_number_cards_are_runtime_custom_and_complete():
 prov=read('qorg/qorg/governance_accountability/provisioning.py')
 assert '"type":"Document Type"' in prov
 assert '"is_standard":0' in prov
 assert '"is_public":1' in prov
 assert prov.count('Number Card:')>=2
def test_every_managed_child_doctype_has_python_controller():
    import re
    base=ROOT/'qorg/qorg/doctype'
    for json_path in base.glob('*/*.json'):
        data=json.loads(json_path.read_text())
        if data.get('module')!='QOrg' or not data.get('istable'):
            continue
        py_path=json_path.with_suffix('.py')
        assert py_path.exists(), data['name']
        source=py_path.read_text()
        class_name=re.sub(r'[^A-Za-z0-9]','',data['name'])
        assert 'from frappe.model.document import Document' in source
        assert f'class {class_name}(Document):' in source

def test_package_has_no_duplicate_doctype_definitions_or_duplicate_fields():
    base=ROOT/'qorg/qorg/doctype'; definitions={}
    for json_path in base.glob('*/*.json'):
        data=json.loads(json_path.read_text()); name=data.get('name')
        definitions.setdefault(name,[]).append(json_path)
        fields=[row.get('fieldname') for row in data.get('fields',[])]
        assert len(fields)==len(set(fields)), name
    assert all(len(paths)==1 for paths in definitions.values()), definitions

def test_procurement_dashboard_patch_does_not_replace_procurement_model():
    folder=ROOT/'qorg/qorg/doctype/procurement_process'
    assert (folder/'procurement_process_dashboard.py').exists()
    assert not (folder/'procurement_process.json').exists()
    assert not (folder/'procurement_process.py').exists()
    assert not (folder/'procurement_process.js').exists()
def test_accountability_settings_has_canonical_name_path_and_controller():
    path=ROOT/'qorg/qorg/doctype/accountability_settings/accountability_settings.json'
    data=json.loads(path.read_text())
    assert data['name']=='Accountability Settings'
    assert data['module']=='QOrg' and data['issingle']==1
    source=(path.parent/'accountability_settings.py').read_text()
    assert 'class AccountabilitySettings(Document):' in source

def test_old_accountability_settings_names_and_paths_are_absent():
    old=('Governance'+' and Accountability Settings','Governance'+'AccountabilitySettings','governance'+'_accountability_settings')
    for path in (ROOT/'qorg').rglob('*'):
        if not path.is_file() or path.suffix not in {'.py','.json','.js','.md','.txt','.html','.css'}:
            continue
        text=path.read_text()
        assert not any(value in text for value in old),path
