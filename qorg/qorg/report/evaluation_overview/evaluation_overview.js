frappe.query_reports['Evaluation Overview']={
 filters:[
  {fieldname:'view',label:__('View'),fieldtype:'Select',options:'Summary\nEmployee\nReviewer\nDepartment\nSource\nRating\nExceptions',default:'Summary',reqd:1},
  {fieldname:'company',label:__('Company'),fieldtype:'Link',options:'Company'}, {fieldname:'appraisal_cycle',label:__('Appraisal Cycle'),fieldtype:'Link',options:'Appraisal Cycle'},
  {fieldname:'employee',label:__('Employee'),fieldtype:'Link',options:'Employee'}, {fieldname:'department',label:__('Department'),fieldtype:'Link',options:'Department'},
  {fieldname:'evaluation_type',label:__('Evaluation Type'),fieldtype:'Link',options:'Evaluation Type'}, {fieldname:'stage',label:__('Stage'),fieldtype:'Select',options:'\nPreparation\nGoal Setting\nGoal Tracking\nSelf-Appraisal Open\nFeedback Collection\nHR Review\nFinalized\nClosed\nReopened\nCancelled'}
 ],
 formatter(value,row,column,data,default_formatter){let out=default_formatter(value,row,column,data);const raw=data&&data[column.fieldname];if(column.fieldtype==='Percent'&&raw!==null&&raw!==undefined)out=`<span class="indicator-pill blue">${out}</span>`;if(['stage','outcome','assignment_status'].includes(column.fieldname)&&raw){const good=['Finalized','Closed','Passed','Submitted'].includes(raw),bad=['Cancelled','Failed','Declined','Overdue'].includes(raw);out=`<span class="indicator-pill ${good?'green':bad?'red':'orange'}">${frappe.utils.escape_html(String(raw))}</span>`;}return out;},
 onload(report){report.page.add_inner_button(__('Reset Filters'),()=>{report.filters.forEach(f=>f.set_value(null));report.get_filter('view').set_value('Summary');report.refresh();});const style=document.createElement('style');style.textContent='.report-summary{display:flex;flex-wrap:wrap;gap:8px}.report-summary .summary-item{min-width:150px;flex:1 1 150px}';document.head.appendChild(style);}
};
