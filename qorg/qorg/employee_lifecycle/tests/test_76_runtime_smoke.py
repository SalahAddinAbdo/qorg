import importlib.util,sys,types
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
class D(dict):
 __getattr__=dict.get
 __setattr__=dict.__setitem__
def modules():
 f=types.ModuleType('frappe');f._=lambda x:x;f.whitelist=lambda *a,**k:(lambda fn:fn);f._dict=lambda x=None:D(x or {});f.get_roles=lambda:['HR User'];f.has_permission=lambda *a,**k:True
 f.utils=types.ModuleType('frappe.utils');f.utils.get_url_to_form=lambda d,n:f'/app/{d}/{n}';f.utils.today=lambda:'2026-11-24'
 j=types.ModuleType('frappe.utils.jinja');j.render_template=lambda text,ctx:text.replace('{{ record_url }}',ctx.get('record_url','')).replace('{{ title }}',ctx.get('title',''))
 f.db=types.SimpleNamespace(get_value=lambda *a,**k:None,exists=lambda *a,**k:False,count=lambda *a,**k:0)
 sys.modules['frappe']=f;sys.modules['frappe.utils']=f.utils;sys.modules['frappe.utils.jinja']=j
 helper=types.ModuleType('qorg.qorg.project_management.report_link_titles');helper.finalize_report_result=lambda x:x;sys.modules['qorg']=types.ModuleType('qorg');sys.modules['qorg.qorg']=types.ModuleType('qorg.qorg');sys.modules['qorg.qorg.project_management']=types.ModuleType('qorg.qorg.project_management');sys.modules['qorg.qorg.project_management.report_link_titles']=helper
 return f
def load(rel,name):
 spec=importlib.util.spec_from_file_location(name,ROOT/rel);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def test_communication_recipient_resolution():
 f=modules();m=load('qorg/qorg/employee_lifecycle/comms.py','comms_smoke')
 assert m._default_recipients('Training Follow-up',D(responsible_user='owner@example.com'))==['owner@example.com']
 assert m._default_recipients('Evaluation Assignment',D(reviewer_user='reviewer@example.com'))==['reviewer@example.com']
 f.db.get_value=lambda *a,**k:'employee@example.com'
 assert m._default_recipients('Appraisal',D(employee='EMP-1'))==['employee@example.com']
 f.get_doc=lambda dt,name:D(employees=[D(employee='E1'),D(employee='E2')])
 assert m._default_recipients('Training Result',D(training_event='EV-1'))==['employee@example.com']
def test_training_report_covers_needs_components_funding_and_exceptions():
 modules();m=load('qorg/qorg/report/training_overview/training_overview.py','training_report_smoke');fields={x['fieldname'] for x in m._columns('Summary')}
 assert {'attendance','pre_score','post_score','practical_score','trainer_score','cert_score','assessment_completion','final_score','result_notes','funding_agreement','budget_line','follow_up_status'}<=fields
 source=(ROOT/'qorg/qorg/report/training_overview/training_overview.py').read_text();assert "def _need_rows" in source and "view=='Exceptions'" in source
def test_evaluation_report_has_true_reviewer_and_source_modes():
 modules();m=load('qorg/qorg/report/evaluation_overview/evaluation_overview.py','evaluation_report_smoke')
 reviewer={x['fieldname'] for x in m._assignment_columns('Reviewer')};source={x['fieldname'] for x in m._assignment_columns('Source')}
 assert {'reviewer','reviewer_name','evaluation_source','status','weight','due_date','overdue'}<=reviewer
 assert 'reviewer' not in source and {'evaluation_source','status','weight','due_date'}<=source
