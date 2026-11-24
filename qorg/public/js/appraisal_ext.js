frappe.ui.form.on('Appraisal', {
  refresh(frm) {
    if (frm.is_new() || !frm.doc.qorg_evaluation_type) return;
    const hr = frappe.user_roles.includes('HR User') || frappe.user_roles.includes('HR Manager') || frappe.user_roles.includes('System Manager');
    const manager = frappe.user_roles.includes('HR Manager') || frappe.user_roles.includes('System Manager');
    if (hr) {
      frm.add_custom_button(__('Generate Assignments'), () => assignment_dialog(frm), __('Evaluation'));
      frm.add_custom_button(__('Recalculate'), () => recalculate(frm), __('Evaluation'));
    }
    frm.add_custom_button(__('Assignments'), () => frappe.set_route('List','Evaluation Assignment',{appraisal:frm.doc.name}), __('Evaluation'));
    const next = {
      'Preparation':['Goal Setting'],
      'Goal Setting':['Goal Tracking'],
      'Goal Tracking':['Self-Appraisal Open','Feedback Collection'],
      'Self-Appraisal Open':['Feedback Collection','Goal Tracking'],
      'Feedback Collection':['HR Review','Self-Appraisal Open'],
      'HR Review':['Finalized','Feedback Collection'],
      'Finalized':['Reopened'],
      'Reopened':['HR Review']
    }[frm.doc.qorg_stage || 'Preparation'] || [];
    next.forEach(stage => {
      if ((['Finalized','Closed','Reopened'].includes(stage) && !manager) || (!manager && !hr)) return;
      frm.add_custom_button(__(stage), () => lifecycle(frm, stage), __('Stage'));
    });
    if (manager && !['Finalized','Closed','Cancelled'].includes(frm.doc.qorg_stage)) frm.add_custom_button(__('Cancel Evaluation'), () => lifecycle(frm,'Cancelled'), __('Stage'));
    if (['Finalized','Closed'].includes(frm.doc.qorg_stage)) frm.set_intro(__('Finalized appraisal content and calculated results are protected.'), 'blue');
  }
});
function assignment_dialog(frm) {
  frappe.prompt([{fieldname:'manual_reviewers',label:__('Manual Reviewers (JSON)'),fieldtype:'Code',options:'JSON',description:__('Example: {"Peers":["HR-EMP-0002"]}')}], values => {
    let reviewers={};if(values.manual_reviewers){try{reviewers=JSON.parse(values.manual_reviewers);}catch(e){frappe.throw(__('Manual Reviewers must be valid JSON.'));}}
    frappe.call({method:'qorg.qorg.employee_lifecycle.perf_api.generate',args:{appraisal:frm.doc.name,manual_reviewers:JSON.stringify(reviewers)},freeze:true}).then(r=>{const x=r.message||{};frappe.msgprint({title:__('Assignments'),message:__('Created: {0}<br>Existing: {1}<br>Unresolved: {2}',[(x.created||[]).length,(x.existing||[]).length,(x.unresolved||[]).map(v=>v.source).join(', ')||__('None')]),wide:true});frm.reload_doc();});
  }, __('Generate Assignments'));
}
function recalculate(frm){frappe.call({method:'qorg.qorg.employee_lifecycle.perf_api.recalculate',args:{appraisal:frm.doc.name},freeze:true}).then(r=>{const x=r.message||{};frappe.msgprint({title:__('Calculated Result'),message:__('Completion: {0}%<br>Final Score: {1}%<br>Rating: {2}<br>Outcome: {3}<br>Provisional: {4}',[flt(x.completion).toFixed(2),flt(x.final_score).toFixed(2),x.rating||'',x.outcome||'',x.provisional?__('Yes'):__('No')])});frm.reload_doc();});}
function lifecycle(frm,stage){
  const requiresReason=['Reopened','Cancelled'].includes(stage);
  if(requiresReason){frappe.prompt([{fieldname:'reason',label:__('Reason'),fieldtype:'Small Text',reqd:1}],v=>call_stage(frm,stage,v.reason),__(stage));}else call_stage(frm,stage);
}
function call_stage(frm,stage,reason){frappe.call({method:'qorg.qorg.employee_lifecycle.perf_api.transition',args:{appraisal:frm.doc.name,stage,reason},freeze:true}).then(()=>frm.reload_doc());}
frappe.ui.form.on('Appraisal', {
  refresh(frm) {
    if (!['Finalized','Closed'].includes(frm.doc.qorg_stage)) return;
    const recommendations=[
      ['qorg_promotion_recommended','Promotion'],['qorg_transfer_recommended','Transfer'],['qorg_salary_recommended','Salary Change'],
      ['qorg_contract_recommended','Contract Renewal'],['qorg_funding_recommended','Funding Change'],['qorg_training_recommended','Training']
    ];
    recommendations.filter(x=>frm.doc[x[0]]).forEach(x=>frm.add_custom_button(__(x[1]),()=>recommendation_dialog(frm,x[1]),__('Prepare Recommendation')));
  }
});
function recommendation_dialog(frm,type){
  const fields=[{fieldname:'effective_date',label:__(type==='Training'?'Target Date':'Effective Date'),fieldtype:'Date',reqd:1},{fieldname:'reason',label:__('Reason / Development Need'),fieldtype:'Small Text',reqd:1}];
  if(type==='Salary Change')fields.push({fieldname:'salary_structure',label:__('Salary Structure'),fieldtype:'Link',options:'Salary Structure',reqd:1});
  if(type==='Training'){fields.push({fieldname:'responsible_person',label:__('Responsible Person'),fieldtype:'Link',options:'User',reqd:1});fields.push({fieldname:'success_measure',label:__('Success Measure'),fieldtype:'Small Text',reqd:1});}
  frappe.prompt(fields,v=>{if(type==='Training')v.target_date=v.effective_date;frappe.call({method:'qorg.qorg.employee_lifecycle.dev_api.recommendation',args:{appraisal:frm.doc.name,recommendation_type:type,values:JSON.stringify(v)},freeze:true}).then(r=>{frappe.set_route('Form',r.message.doctype,r.message.name);});},__('Prepare {0}',[type]));
}
