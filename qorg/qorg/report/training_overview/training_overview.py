import frappe
from frappe import _
from qorg.qorg.project_management.report_link_titles import finalize_report_result

def execute(filters=None):
 f=frappe._dict(filters or {}); view=f.get('view') or 'Summary'; columns,rows=(_need_rows(f) if view=='Needs' else (_columns(view),_rows(f,view))); summary=_summary(rows); chart=_chart(rows,view);message=None if rows else _('No training records match the selected filters.')
 return finalize_report_result((columns,rows,message,chart,summary,1))

def _rows(f,view):
 cond={};
 if f.company:cond['company']=f.company
 events=frappe.get_all('Training Event',filters=cond,fields=['name','event_name','training_program','company','start_time','end_time','event_status','qorg_project','qorg_funding_agreement','qorg_budget_line'],order_by='start_time desc')
 result=[]
 for e in events:
  if f.training_event and e.name!=f.training_event:continue
  if f.training_program and e.training_program!=f.training_program:continue
  if f.project and e.qorg_project!=f.project:continue
  if f.from_date and e.end_time and str(e.end_time)[:10]<str(f.from_date):continue
  if f.to_date and e.start_time and str(e.start_time)[:10]>str(f.to_date):continue
  result_name=frappe.db.get_value('Training Result',{'training_event':e.name,'docstatus':['<',2]},'name')
  participants=frappe.get_all('Training Event Employee',filters={'parent':e.name},fields=['employee','qorg_attendance_percentage'])
  result_rows={r.employee:r for r in frappe.get_all('Training Result Employee',filters={'parent':result_name},fields=['employee','qorg_attendance_percentage','qorg_pre_score','qorg_post_score','qorg_practical_score','qorg_trainer_score','qorg_cert_score','qorg_assessment_completion','qorg_final_score','qorg_result','qorg_result_notes','qorg_certificate_eligible'])} if result_name else {}
  for p in participants:
   if f.employee and p.employee!=f.employee:continue
   if f.department and p.department!=f.department:continue
   emp=frappe.db.get_value('Employee',p.employee,['employee_name','department'],as_dict=True) or frappe._dict();p.employee_name=emp.employee_name;p.department=emp.department
   rr=result_rows.get(p.employee,frappe._dict());fu=frappe.db.get_value('Training Follow-up',{'training_event':e.name,'employee':p.employee,'status':['!=','Cancelled']},['name','status','due_date'],as_dict=True) or frappe._dict()
   status=rr.qorg_result or 'Pending'
   if f.status and f.status not in {status,fu.status}:continue
   row={'training_event':e.name,'event_name':e.event_name,'training_program':e.training_program,'project':e.qorg_project,'funding_agreement':e.qorg_funding_agreement,'budget_line':e.qorg_budget_line,'company':e.company,'start_date':e.start_time,'employee':p.employee,'employee_name':p.employee_name,'department':p.department,'attendance':p.qorg_attendance_percentage,'pre_score':rr.qorg_pre_score,'post_score':rr.qorg_post_score,'practical_score':rr.qorg_practical_score,'trainer_score':rr.qorg_trainer_score,'cert_score':rr.qorg_cert_score,'assessment_completion':rr.qorg_assessment_completion,'final_score':rr.qorg_final_score,'result':status,'result_notes':rr.qorg_result_notes,'certificate':rr.qorg_certificate_eligible,'follow_up':fu.name,'follow_up_status':fu.status or 'Not Required','due_date':fu.due_date}
   if view=='Exceptions' and status not in {'Incomplete','Failed','Not Eligible','Pending'} and fu.status!='Overdue':continue
   result.append(row)
 return result

def _need_rows(f):
 cond={}
 for key in ('company','department','need_source'):
  if f.get(key):cond[key]=f.get(key)
 if f.need_status:cond['status']=f.need_status
 if f.from_date and f.to_date:cond['request_date']=['between',[f.from_date,f.to_date]]
 elif f.from_date:cond['request_date']=['>=',f.from_date]
 elif f.to_date:cond['request_date']=['<=',f.to_date]
 rows=frappe.get_list('Training Need Request',filters=cond,fields=['name','training_need_title','request_date','company','department','need_source','request_scope','priority','mandatory_training','expected_participants','estimated_cost','currency','project','funding_agreement','status','training_program','training_event'],order_by='request_date desc')
 cols=[{'label':_('Training Need'),'fieldname':'name','fieldtype':'Link','options':'Training Need Request','width':170},{'label':_('Title'),'fieldname':'training_need_title','width':220},{'label':_('Date'),'fieldname':'request_date','fieldtype':'Date','width':100},{'label':_('Department'),'fieldname':'department','fieldtype':'Link','options':'Department','width':140},{'label':_('Source'),'fieldname':'need_source','width':160},{'label':_('Scope'),'fieldname':'request_scope','width':140},{'label':_('Priority'),'fieldname':'priority','width':90},{'label':_('Mandatory'),'fieldname':'mandatory_training','fieldtype':'Check','width':85},{'label':_('Participants'),'fieldname':'expected_participants','fieldtype':'Int','width':90},{'label':_('Estimated Cost'),'fieldname':'estimated_cost','fieldtype':'Currency','options':'currency','width':115},{'label':_('Project'),'fieldname':'project','fieldtype':'Link','options':'Project','width':130},{'label':_('Status'),'fieldname':'status','width':110},{'label':_('Program'),'fieldname':'training_program','fieldtype':'Link','options':'Training Program','width':145},{'label':_('Event'),'fieldname':'training_event','fieldtype':'Link','options':'Training Event','width':145}]
 return cols,rows

def _columns(view):
 return [{'label':_('Event'),'fieldname':'training_event','fieldtype':'Link','options':'Training Event','width':170},{'label':_('Program'),'fieldname':'training_program','fieldtype':'Link','options':'Training Program','width':150},{'label':_('Project'),'fieldname':'project','fieldtype':'Link','options':'Project','width':140},{'label':_('Funding Agreement'),'fieldname':'funding_agreement','fieldtype':'Link','options':'Funding Agreement','width':145},{'label':_('Budget Line'),'fieldname':'budget_line','fieldtype':'Link','options':'Budget Line','width':130},{'label':_('Employee'),'fieldname':'employee','fieldtype':'Link','options':'Employee','width':150},{'label':_('Employee Name'),'fieldname':'employee_name','width':180},{'label':_('Department'),'fieldname':'department','fieldtype':'Link','options':'Department','width':150},{'label':_('Attendance'),'fieldname':'attendance','fieldtype':'Percent','width':95},{'label':_('Pre Score'),'fieldname':'pre_score','fieldtype':'Percent','width':85},{'label':_('Post Score'),'fieldname':'post_score','fieldtype':'Percent','width':85},{'label':_('Practical'),'fieldname':'practical_score','fieldtype':'Percent','width':85},{'label':_('Trainer'),'fieldname':'trainer_score','fieldtype':'Percent','width':85},{'label':_('Certification'),'fieldname':'cert_score','fieldtype':'Percent','width':95},{'label':_('Assessment Completion'),'fieldname':'assessment_completion','fieldtype':'Percent','width':110},{'label':_('Final Score'),'fieldname':'final_score','fieldtype':'Percent','width':95},{'label':_('Result'),'fieldname':'result','width':110},{'label':_('Result Notes'),'fieldname':'result_notes','width':220},{'label':_('Certificate'),'fieldname':'certificate','fieldtype':'Check','width':85},{'label':_('Follow-up'),'fieldname':'follow_up','fieldtype':'Link','options':'Training Follow-up','width':140},{'label':_('Follow-up Status'),'fieldname':'follow_up_status','width':120},{'label':_('Due Date'),'fieldname':'due_date','fieldtype':'Date','width':105}]

def _summary(rows):
 if rows and 'training_need_title' in rows[0]:return [{'label':_('Needs'),'value':len(rows),'indicator':'blue'},{'label':_('Approved'),'value':sum(r.status=='Approved' for r in rows),'indicator':'green'},{'label':_('Pending'),'value':sum(r.status in {'Draft','Pending HR Review','Pending Approval'} for r in rows),'indicator':'orange'},{'label':_('Critical'),'value':sum(r.priority=='Critical' for r in rows),'indicator':'red'}]
 return [{'label':_('Participants'),'value':len(rows),'indicator':'blue'},{'label':_('Passed'),'value':sum(r['result']=='Passed' for r in rows),'indicator':'green'},{'label':_('Exceptions'),'value':sum(r['result'] in {'Incomplete','Failed','Not Eligible','Pending'} or r['follow_up_status']=='Overdue' for r in rows),'indicator':'red'},{'label':_('Average Score'),'value':round(sum(float(r['final_score'] or 0) for r in rows)/len(rows),1) if rows else 0,'indicator':'orange','datatype':'Percent'}]

def _chart(rows,view):
 field={'Needs':'status','Department':'department','Event':'event_name','Program':'training_program','Project / Funding':'funding_agreement','Employee':'result','Exceptions':'result'}.get(view,'result');counts={}
 for r in rows:counts[r.get(field) or _('Not Specified')]=counts.get(r.get(field) or _('Not Specified'),0)+1
 return {'data':{'labels':list(counts),'datasets':[{'name':_('Records'),'values':list(counts.values())}]},'type':'donut' if view in {'Summary','Exceptions'} else 'bar','height':300,'colors':['#176B87','#2E7D32','#D7A83E','#C62828','#6A1B9A']}
