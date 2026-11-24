frappe.query_reports['Training Overview']={
 filters:[
  {fieldname:'view',label:__('View'),fieldtype:'Select',options:'Summary\nNeeds\nEmployee\nEvent\nDepartment\nProgram\nProject / Funding\nExceptions',default:'Summary',reqd:1},
  {fieldname:'company',label:__('Company'),fieldtype:'Link',options:'Company'},
  {fieldname:'from_date',label:__('From Date'),fieldtype:'Date'}, {fieldname:'to_date',label:__('To Date'),fieldtype:'Date'},
  {fieldname:'employee',label:__('Employee'),fieldtype:'Link',options:'Employee'}, {fieldname:'department',label:__('Department'),fieldtype:'Link',options:'Department'},
  {fieldname:'project',label:__('Project'),fieldtype:'Link',options:'Project'}, {fieldname:'training_program',label:__('Training Program'),fieldtype:'Link',options:'Training Program'},
  {fieldname:'training_event',label:__('Training Event'),fieldtype:'Link',options:'Training Event'}, {fieldname:'need_status',label:__('Need Status'),fieldtype:'Select',options:'\nDraft\nPending HR Review\nPending Approval\nApproved\nReturned\nRejected\nConverted\nCancelled',depends_on:"eval:doc.view=='Needs'"},
  {fieldname:'need_source',label:__('Need Source'),fieldtype:'Select',options:'\nAppraisal Recommendation\nCompetency Gap\nEmployee Request\nManager Request\nHR Requirement\nPolicy or Compliance Requirement\nProject Requirement\nAnnual Training Plan\nContract Requirement\nOther'},
  {fieldname:'status',label:__('Result / Follow-up Status'),fieldtype:'Select',depends_on:"eval:doc.view!='Needs'",options:'\nPending\nIncomplete\nPassed\nFailed\nNot Eligible\nOverdue'}
 ],
 formatter(value,row,column,data,default_formatter){let out=default_formatter(value,row,column,data);const raw=data&&data[column.fieldname];if(column.fieldtype==='Percent'&&raw!==null&&raw!==undefined)out=`<span class="indicator-pill blue">${out}</span>`;if(['status','result','follow_up_status'].includes(column.fieldname)&&raw){const good=['Passed','Completed'].includes(raw),bad=['Failed','Not Eligible','Overdue'].includes(raw);out=`<span class="indicator-pill ${good?'green':bad?'red':'orange'}">${frappe.utils.escape_html(String(raw))}</span>`;}return out;},
 onload(report){report.page.add_inner_button(__('Reset Filters'),()=>{report.filters.forEach(f=>f.set_value(null));report.get_filter('view').set_value('Summary');report.refresh();});const style=document.createElement('style');style.textContent='.report-summary{display:flex;flex-wrap:wrap;gap:8px}.report-summary .summary-item{min-width:150px;flex:1 1 150px}';document.head.appendChild(style);}
};
