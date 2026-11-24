import importlib.util,sys,types
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]

def stub():
 f=types.ModuleType('frappe');f._=lambda x:x;f.whitelist=lambda *a,**k:(lambda fn:fn);f.PermissionError=PermissionError;f.get_roles=lambda:[];f.session=types.SimpleNamespace(user='tester');f._dict=lambda x:types.SimpleNamespace(**x)
 u=types.ModuleType('frappe.utils');u.flt=lambda x:float(x or 0);u.add_days=lambda d,n:d;u.getdate=lambda x:x;u.now_datetime=lambda:'2026-01-01';u.today=lambda:'2026-01-01';f.utils=u
 sys.modules['frappe']=f;sys.modules['frappe.utils']=u
 return f

def load(name):
 stub();p=ROOT/f'qorg/qorg/employee_lifecycle/{name}.py';spec=importlib.util.spec_from_file_location('x_'+name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def obj(**kw):
 class O(types.SimpleNamespace):
  def get(self,k,d=None):return getattr(self,k,d)
 return O(**kw)

def test_score_types():
 m=load('performance');policy=obj(source_score_max=5)
 assert m._normalize_by_definition(80,obj(score_type='Percentage',score_max=0,pass_score=0),policy)==80
 assert m._normalize_by_definition(4,obj(score_type='Numeric Scale',score_max=5,pass_score=0),policy)==80
 assert m._normalize_by_definition(1,obj(score_type='Pass/Fail',score_max=0,pass_score=1),policy)==100
 assert m._normalize_by_definition(0,obj(score_type='Pass/Fail',score_max=0,pass_score=1),policy)==0

def test_completed_weight_can_finalize_at_configured_minimum():
 m=load('performance');m._rating=lambda scale,score:('Good','Passed',False);m.now_datetime=lambda:'now'
 rows=[{'source':'Manager','weight':70,'completion':100,'meets_minimum':1,'status':'Complete','source_score':80,'policy_applied':'Completed Weight'}, {'source':'Peers','weight':30,'completion':0,'meets_minimum':0,'status':'Missing','source_score':0,'policy_applied':'Completed Weight'}]
 m._source_result=lambda doc,policy,definition:rows.pop(0)
 policy=obj(sources=[obj(),obj()],completion_policy='Completed Weight',min_completion=70,rating_scale='R',name='P')
 result=m._calculate(obj(name='A'),policy)
 assert result['completion']==70 and not result['provisional'] and result['final_score']==80

def test_source_strict_override_blocks_flexible_policy():
 m=load('performance');m._rating=lambda scale,score:('','Passed',False);m.now_datetime=lambda:'now'
 rows=[{'source':'Manager','weight':70,'completion':100,'meets_minimum':1,'status':'Complete','source_score':80,'policy_applied':'Completed Weight'}, {'source':'Peers','weight':30,'completion':0,'meets_minimum':0,'status':'Missing','source_score':0,'policy_applied':'Strict Completion'}]
 m._source_result=lambda doc,policy,definition:rows.pop(0)
 result=m._calculate(obj(name='A'),obj(sources=[obj(),obj()],completion_policy='Completed Weight',min_completion=70,rating_scale='R',name='P'))
 assert result['provisional'] and result['outcome']=='Incomplete'

def test_required_vs_minimum_review_completion_is_distinct():
 source=(ROOT/'qorg/qorg/employee_lifecycle/performance.py').read_text()
 assert 'completed * 100 / required' in source and 'completed >= minimum' in source

def test_training_multiple_components_and_mandatory_pass():
 m=load('training');rules=[{'component':'Attendance','weight':20,'required':1,'must_pass':1,'pass_score':75},{'component':'Post-Assessment','weight':40,'required':1,'must_pass':1,'pass_score':60},{'component':'Practical','weight':40,'required':1,'must_pass':0,'pass_score':60}]
 selected={'Post-Assessment':obj(percentage=80,passed=1),'Practical':obj(percentage=70,passed=1)}
 r=m.calculate_training_result(80,rules,selected,60,True,False)
 assert r['final_score']==76 and r['result']=='Passed' and r['completion']==100

def test_training_missing_required_and_feedback():
 m=load('training');rules=[{'component':'Post-Assessment','weight':100,'required':1,'must_pass':1,'pass_score':60}]
 r=m.calculate_training_result(100,rules,{},60,False,True)
 assert r['result']=='Incomplete' and not r['passed'] and len(r['blockers'])>=2

def test_training_required_fail_blocks_even_high_average():
 m=load('training');rules=[{'component':'Attendance','weight':10,'required':1,'must_pass':1,'pass_score':75},{'component':'Certification Exam','weight':90,'required':1,'must_pass':1,'pass_score':60}]
 r=m.calculate_training_result(100,rules,{'Certification Exam':obj(percentage=59,passed=0)},50,True,False)
 assert r['result']=='Failed' and not r['passed']

def test_pre100_deterioration_is_negative():
 m=load('training');assert m._improvement_percentage(obj(percentage=100),obj(percentage=80))==-20
