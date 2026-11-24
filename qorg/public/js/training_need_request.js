frappe.ui.form.on('Training Need Request', {
  setup(frm) {
    frm.set_query('branch', () => ({ filters: frm.doc.company ? { company: frm.doc.company } : {} }));
    frm.set_query('department', () => ({ filters: Object.assign({is_group: 0}, frm.doc.company ? { company: frm.doc.company } : {}) }));
    frm.set_query('cost_center', () => ({ filters: { company: frm.doc.company || '', is_group: 0 } }));
    frm.set_query('project', () => ({ filters: Object.assign({status: 'Open'}, frm.doc.company ? { company: frm.doc.company } : {}) }));
    frm.set_query('funding_agreement', () => ({ filters: { company: frm.doc.company || '', status: ['not in', ['Closed','Cancelled']] } }));
    frm.set_query('budget_line', () => ({ filters: { project: frm.doc.project || '', is_group: 0, status: ['not in', ['Closed','Cancelled']] } }));
    frm.set_query('requested_for_employee', () => ({ filters: { company: frm.doc.company || '', status: 'Active' } }));
    frm.set_query('employee', 'participants', () => ({ filters: { company: frm.doc.company || '', status: 'Active' } }));
    frm.set_query('source_doctype', () => ({ filters: { name: ['in', allowed_source_doctypes(frm.doc.need_source)] } }));
    frm.set_query('source_document', () => source_document_query(frm));
  },
  refresh(frm) {
    render_actions(frm);
    if (!frm.is_new() && !['Draft', 'Returned'].includes(frm.doc.status)) {
      frm.set_intro(__('This request is governed by lifecycle actions. Return it before changing protected need, scope, or funding fields.'), 'blue');
    }
  },
  need_source(frm) {
    const allowed = allowed_source_doctypes(frm.doc.need_source);
    if (frm.doc.source_doctype && !allowed.includes(frm.doc.source_doctype)) {
      frm.set_value('source_doctype', '');
      frm.set_value('source_document', '');
    }
    if (allowed.length === 1) frm.set_value('source_doctype', allowed[0]);
  },
  request_scope(frm) {
    if (frm.doc.request_scope !== 'Named Group') frm.clear_table('participants');
  },
  company(frm) {
    ['branch','department','project','cost_center','funding_agreement','budget_line','requested_for_employee'].forEach(f => frm.set_value(f, ''));
  },
  funding_required(frm) {
    if (!frm.doc.funding_required) ['estimated_cost','currency','cost_center','funding_agreement','budget_line','funding_notes'].forEach(f => frm.set_value(f, ''));
  }
});

function allowed_source_doctypes(source) {
  return {
    'Appraisal Recommendation': ['Appraisal'],
    'Competency Gap': ['Employee Skill Map'],
    'Policy or Compliance Requirement': ['Employee Document Requirement'],
    'Contract Requirement': ['Contract Template']
  }[source] || ['Appraisal','Employee Skill Map','Employee Performance Feedback','Employee Document Requirement','Contract Template','Project','Goal'];
}

function render_actions(frm) {
  if (frm.is_new()) return;
  const roles = frappe.user_roles || [];
  if (['Draft','Returned'].includes(frm.doc.status)) add_action(frm, __('Submit for HR Review'), 'submit_for_hr_review');
  if (frm.doc.status === 'Pending HR Review' && roles.includes('HR User')) add_action(frm, __('Send for Approval'), 'send_for_approval');
  if (['Pending HR Review','Pending Approval'].includes(frm.doc.status) && (roles.includes('HR User') || roles.includes('HR Manager'))) {
    frm.add_custom_button(__('Return'), () => reason_action(frm, 'return'), __('Lifecycle'));
  }
  if (frm.doc.status === 'Pending Approval' && roles.includes('HR Manager')) add_action(frm, __('Approve'), 'approve');
  if (['Pending HR Review','Pending Approval'].includes(frm.doc.status) && roles.includes('HR Manager')) {
    frm.add_custom_button(__('Reject'), () => reason_action(frm, 'reject'), __('Lifecycle'));
  }
  if (['Draft','Returned','Approved'].includes(frm.doc.status)) add_action(frm, __('Cancel Request'), 'cancel');
  if (frm.doc.status === 'Approved' && (roles.includes('HR User') || roles.includes('HR Manager'))) {
    frm.add_custom_button(__('Preview Participants'), () => preview_participants(frm), __('Conversion'));
    frm.add_custom_button(__('Convert'), () => conversion_dialog(frm), __('Conversion'));
  }
  if (frm.doc.training_program) frm.add_custom_button(__('Training Program'), () => frappe.set_route('Form','Training Program',frm.doc.training_program), __('Open'));
  if (frm.doc.training_event) frm.add_custom_button(__('Training Event'), () => frappe.set_route('Form','Training Event',frm.doc.training_event), __('Open'));
}
function add_action(frm, label, action) {
  frm.add_custom_button(label, () => call_transition(frm, action), __('Lifecycle'));
}
function call_transition(frm, action, reason) {
  frappe.call({method:'qorg.qorg.employee_lifecycle.learning_api.transition',args:{name:frm.doc.name,action,reason},freeze:true}).then(() => frm.reload_doc());
}
function reason_action(frm, action) {
  frappe.prompt([{fieldname:'reason',label:__('Reason'),fieldtype:'Small Text',reqd:1}], values => call_transition(frm, action, values.reason), __(action === 'reject' ? 'Reject Request' : 'Return Request'));
}
function preview_participants(frm) {
  frappe.call({method:'qorg.qorg.employee_lifecycle.learning_api.preview_participants',args:{name:frm.doc.name}}).then(r => {
    const data=r.message||{};
    const shown=(data.employees||[]).map(x=>frappe.utils.escape_html(x)).join('<br>');
    frappe.msgprint({title:__('Resolved Participants: {0}',[data.count||0]),message:shown+(data.truncated?'<br><b>'+__('Only the first 200 are shown.')+'</b>':''),wide:true});
  });
}
function conversion_dialog(frm) {
  const dialog = new frappe.ui.Dialog({title:__('Convert Training Need'),fields:[
    {fieldname:'mode',label:__('Conversion Mode'),fieldtype:'Select',options:'Link Existing Program\nCreate Training Program\nCreate Training Event',reqd:1},
    {fieldname:'existing_program',label:__('Existing Training Program'),fieldtype:'Link',options:'Training Program',depends_on:"eval:doc.mode=='Link Existing Program'"},
    {fieldname:'event_section',label:__('Training Event'),fieldtype:'Section Break',depends_on:"eval:doc.mode=='Create Training Event'"},
    {fieldname:'event_name',label:__('Event Name'),fieldtype:'Data',depends_on:"eval:doc.mode=='Create Training Event'"},
    {fieldname:'start_time',label:__('Start Time'),fieldtype:'Datetime',depends_on:"eval:doc.mode=='Create Training Event'",mandatory_depends_on:"eval:doc.mode=='Create Training Event'"},
    {fieldname:'end_time',label:__('End Time'),fieldtype:'Datetime',depends_on:"eval:doc.mode=='Create Training Event'",mandatory_depends_on:"eval:doc.mode=='Create Training Event'"},
    {fieldname:'location',label:__('Location / Online Link'),fieldtype:'Data',depends_on:"eval:doc.mode=='Create Training Event'"}
  ],primary_action_label:__('Convert'),primary_action(values){
    const event_values={event_name:values.event_name,start_time:values.start_time,end_time:values.end_time,location:values.location};
    frappe.call({method:'qorg.qorg.employee_lifecycle.learning_api.convert',args:{name:frm.doc.name,mode:values.mode,existing_program:values.existing_program,event_values:JSON.stringify(event_values)},freeze:true}).then(()=>{dialog.hide();frm.reload_doc();});
  }});
  dialog.show();
}

function source_document_query(frm) {
  const dt=frm.doc.source_doctype;
  if (!dt) return {filters:{name:''}};
  const filters={};
  if (['Appraisal','Employee Skill Map'].includes(dt) && frm.doc.requested_for_employee) filters.employee=frm.doc.requested_for_employee;
  if (dt==='Appraisal') filters.docstatus=1;
  if (dt==='Employee Document Requirement') filters.is_active=1;
  return {filters};
}
