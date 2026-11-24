import frappe
from frappe import _
from qorg.qorg.project_management.report_link_titles import finalize_report_result

def execute(filters=None):
 f=frappe._dict(filters or {});view=f.get('view') or 'Summary'
 if view in {'Reviewer','Source'}: columns,rows=_assignment_rows(f,view)
 else: columns,rows=_appraisal_rows(f,view)
 return finalize_report_result((columns,rows,None if rows else _('No evaluation records match the selected filters.'),_chart(rows,view),_summary(rows,view),1))

def _filters(f):
 cond={}
 for key,field in [('company','company'),('appraisal_cycle','appraisal_cycle'),('employee','employee'),('department','department'),('evaluation_type','qorg_evaluation_type'),('stage','qorg_stage')]:
  if f.get(key):cond[field]=f.get(key)
 return cond

def _appraisal_rows(f,view):
 rows=frappe.get_list('Appraisal',filters=_filters(f),fields=['name','employee','employee_name','department','appraisal_cycle','qorg_evaluation_type','qorg_stage','qorg_completion','qorg_final_score','qorg_rating','qorg_outcome','qorg_provisional','qorg_assignment_total','qorg_assignment_submitted','qorg_assignment_pending'],order_by='end_date desc')
 out=[]
 for r in rows:
  r.assignment_status='Complete' if not r.qorg_assignment_pending and r.qorg_assignment_total else ('Pending' if r.qorg_assignment_pending else 'Not Generated')
  r.overdue=frappe.db.count('Evaluation Assignment',{'appraisal':r.name,'status':['in',['Assigned','In Progress']],'due_date':['<',frappe.utils.today()]})
  if view=='Exceptions' and not (r.qorg_provisional or r.qorg_assignment_pending or r.overdue or r.qorg_outcome in {'Incomplete','Failed','Development Plan'}):continue
  out.append(r)
 return _appraisal_columns(),out

def _assignment_rows(f,view):
 cond={}
 for k in ('appraisal_cycle','employee','evaluation_type'):
  if f.get(k):cond[k]=f.get(k)
 assignments=frappe.get_list('Evaluation Assignment',filters=cond,fields=['name','appraisal','employee','employee_name','reviewer','reviewer_name','evaluation_source','status','assigned_on','due_date','submitted_on','anonymous','weight'],order_by='due_date asc')
 rows=[]
 for r in assignments:
  app=frappe.db.get_value('Appraisal',r.appraisal,['company','department','qorg_stage'],as_dict=True) or frappe._dict()
  if f.company and app.company!=f.company:continue
  if f.department and app.department!=f.department:continue
  if f.stage and app.qorg_stage!=f.stage:continue
  r.department=app.department;r.stage=app.qorg_stage;r.overdue=1 if r.status in {'Assigned','In Progress'} and r.due_date and r.due_date<frappe.utils.today() else 0
  # protect anonymous reviewer identity outside HR Manager/System Manager
  if r.anonymous and not {'HR Manager','System Manager'}.intersection(frappe.get_roles()):r.reviewer=r.reviewer_name=_('Anonymous')
  rows.append(r)
 return _assignment_columns(view),rows

def _appraisal_columns():
 return [{'label':_('Appraisal'),'fieldname':'name','fieldtype':'Link','options':'Appraisal','width':170},{'label':_('Employee'),'fieldname':'employee','fieldtype':'Link','options':'Employee','width':150},{'label':_('Employee Name'),'fieldname':'employee_name','width':180},{'label':_('Department'),'fieldname':'department','fieldtype':'Link','options':'Department','width':150},{'label':_('Cycle'),'fieldname':'appraisal_cycle','fieldtype':'Link','options':'Appraisal Cycle','width':150},{'label':_('Stage'),'fieldname':'qorg_stage','width':125},{'label':_('Completion'),'fieldname':'qorg_completion','fieldtype':'Percent','width':95},{'label':_('Final Score'),'fieldname':'qorg_final_score','fieldtype':'Percent','width':95},{'label':_('Rating'),'fieldname':'qorg_rating','width':120},{'label':_('Outcome'),'fieldname':'qorg_outcome','width':125},{'label':_('Pending'),'fieldname':'qorg_assignment_pending','fieldtype':'Int','width':80},{'label':_('Overdue'),'fieldname':'overdue','fieldtype':'Int','width':80}]

def _assignment_columns(view):
 cols=[{'label':_('Assignment'),'fieldname':'name','fieldtype':'Link','options':'Evaluation Assignment','width':170},{'label':_('Appraisal'),'fieldname':'appraisal','fieldtype':'Link','options':'Appraisal','width':160},{'label':_('Employee'),'fieldname':'employee','fieldtype':'Link','options':'Employee','width':145},{'label':_('Employee Name'),'fieldname':'employee_name','width':170}]
 if view=='Reviewer':cols += [{'label':_('Reviewer'),'fieldname':'reviewer','fieldtype':'Link','options':'Employee','width':145},{'label':_('Reviewer Name'),'fieldname':'reviewer_name','width':170}]
 cols += [{'label':_('Source'),'fieldname':'evaluation_source','width':135},{'label':_('Status'),'fieldname':'status','width':105},{'label':_('Weight'),'fieldname':'weight','fieldtype':'Percent','width':85},{'label':_('Due Date'),'fieldname':'due_date','fieldtype':'Date','width':105},{'label':_('Overdue'),'fieldname':'overdue','fieldtype':'Check','width':75}]
 return cols

def _summary(rows,view):
 if view in {'Reviewer','Source'}:return [{'label':_('Assignments'),'value':len(rows),'indicator':'blue'},{'label':_('Submitted'),'value':sum(r.status=='Submitted' for r in rows),'indicator':'green'},{'label':_('Pending'),'value':sum(r.status in {'Assigned','In Progress'} for r in rows),'indicator':'orange'},{'label':_('Overdue'),'value':sum(r.overdue for r in rows),'indicator':'red'}]
 return [{'label':_('Appraisals'),'value':len(rows),'indicator':'blue'},{'label':_('Closed / Finalized'),'value':sum(r.qorg_stage in {'Finalized','Closed'} for r in rows),'indicator':'green'},{'label':_('Pending Feedback'),'value':sum(int(r.qorg_assignment_pending or 0) for r in rows),'indicator':'orange'},{'label':_('Exceptions'),'value':sum(bool(r.qorg_provisional or r.overdue or r.qorg_outcome in {'Incomplete','Failed','Development Plan'}) for r in rows),'indicator':'red'}]

def _chart(rows,view):
 field={'Reviewer':'reviewer_name','Source':'evaluation_source','Department':'department','Rating':'qorg_rating','Employee':'qorg_outcome','Exceptions':'qorg_outcome'}.get(view,'qorg_stage');counts={}
 for r in rows:counts[r.get(field) or _('Not Specified')]=counts.get(r.get(field) or _('Not Specified'),0)+1
 return {'data':{'labels':list(counts),'datasets':[{'name':_('Records'),'values':list(counts.values())}]},'type':'donut' if view in {'Summary','Rating','Exceptions'} else 'bar','height':300,'colors':['#176B87','#2E7D32','#D7A83E','#C62828','#6A1B9A']}
