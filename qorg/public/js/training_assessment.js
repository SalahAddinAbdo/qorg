frappe.ui.form.on('Training Assessment', {
  setup(frm) {
    frm.set_query('training_event', () => ({filters:{docstatus:1,event_status:['not in',['Cancelled']]}}));
    frm.set_query('employee', () => ({query:'qorg.qorg.employee_lifecycle.training_query.event_employees',filters:{training_event:frm.doc.training_event||''}}));
    frm.set_query('assessor', () => ({filters:{enabled:1,user_type:'System User'}}));
    frm.set_query('evidence', () => ({filters:{subject_doctype:'Employee',subject_name:frm.doc.employee||'',status:'Verified'}}));
  },
  refresh(frm) {
    if (frm.is_new()) return;
    if (frm.doc.status==='Draft') frm.add_custom_button(__('Submit Assessment'),()=>frappe.call({method:'qorg.qorg.employee_lifecycle.training_api.submit',args:{name:frm.doc.name},freeze:true}).then(()=>frm.reload_doc()),__('Actions'));
    if (frm.doc.status==='Submitted' && (frappe.user_roles.includes('HR User')||frappe.user_roles.includes('HR Manager'))) frm.add_custom_button(__('Cancel Assessment'),()=>frappe.prompt([{fieldname:'reason',label:__('Reason'),fieldtype:'Small Text',reqd:1}],v=>frappe.call({method:'qorg.qorg.employee_lifecycle.training_api.cancel',args:{name:frm.doc.name,reason:v.reason},freeze:true}).then(()=>frm.reload_doc()),__('Cancel Assessment')),__('Actions'));
  },
  training_event(frm){frm.set_value('employee','');},
  maximum_score: calculate,
  score: calculate,
  passing_percentage: calculate
});
function calculate(frm){const max=flt(frm.doc.maximum_score),score=flt(frm.doc.score),pass=flt(frm.doc.passing_percentage);const pct=max>0?score*100/max:0;frm.set_value('percentage',pct);frm.set_value('passed',pct>=pass?1:0);}
