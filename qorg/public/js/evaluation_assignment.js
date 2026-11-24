frappe.ui.form.on('Evaluation Assignment', {
  setup(frm) {
    frm.set_query('reviewer',()=>({query:'qorg.qorg.employee_lifecycle.perf_query.reviewers',filters:{employee:frm.doc.employee||'',source:frm.doc.evaluation_source||'',department:frm.doc.related_department||''}}));
    frm.set_query('appraisal_cycle',()=>({filters:{status:['not in',['Completed','Cancelled']]}}));
    frm.set_query('appraisal',()=>({filters:{appraisal_cycle:frm.doc.appraisal_cycle||'',docstatus:['<',2]}}));
    frm.set_query('evaluation_type',()=>({filters:{active:1}}));
    frm.set_query('feedback',()=>({filters:{appraisal:frm.doc.appraisal||'',employee:frm.doc.employee||''}}));
  },
  refresh(frm) {
    if(frm.is_new())return;
    const current=frappe.session.user===frm.doc.reviewer_user;
    if(['Assigned','In Progress'].includes(frm.doc.status) && current) {
      frm.add_custom_button(__('Open Feedback'),()=>frappe.call({method:'qorg.qorg.employee_lifecycle.perf_api.feedback',args:{assignment:frm.doc.name},freeze:true}).then(r=>frappe.set_route('Form','Employee Performance Feedback',r.message.feedback)),__('Actions'));
      frm.add_custom_button(__('Decline'),()=>decline(frm),__('Actions'));
    }
    if(['Assigned','In Progress','Declined'].includes(frm.doc.status) && (frappe.user_roles.includes('HR User')||frappe.user_roles.includes('HR Manager'))) frm.add_custom_button(__('Replace Reviewer'),()=>replace_reviewer(frm),__('Actions'));
    if(frm.doc.feedback) frm.add_custom_button(__('Feedback'),()=>frappe.set_route('Form','Employee Performance Feedback',frm.doc.feedback),__('Open'));
  },
  appraisal_cycle(frm){frm.set_value('appraisal','');},
  appraisal(frm){if(!frm.doc.appraisal)return;frappe.db.get_value('Appraisal',frm.doc.appraisal,['employee','qorg_evaluation_type']).then(r=>{frm.set_value('employee',r.message.employee);frm.set_value('evaluation_type',r.message.qorg_evaluation_type);});}
});
function decline(frm){frappe.prompt([{fieldname:'reason',label:__('Reason'),fieldtype:'Small Text',reqd:1},{fieldname:'conflict',label:__('Conflict of Interest'),fieldtype:'Check'}],v=>frappe.call({method:'qorg.qorg.employee_lifecycle.perf_api.decline',args:{name:frm.doc.name,reason:v.reason,conflict:v.conflict?1:0},freeze:true}).then(()=>frm.reload_doc()),__('Decline Assignment'));}
function replace_reviewer(frm){frappe.prompt([{fieldname:'reviewer',label:__('New Reviewer'),fieldtype:'Link',options:'Employee',reqd:1,get_query:()=>({filters:{status:'Active'}})},{fieldname:'reason',label:__('Reason'),fieldtype:'Small Text',reqd:1}],v=>frappe.call({method:'qorg.qorg.employee_lifecycle.perf_api.replace',args:{name:frm.doc.name,reviewer:v.reviewer,reason:v.reason},freeze:true}).then(r=>frappe.set_route('Form','Evaluation Assignment',r.message.new)),__('Replace Reviewer'));}
