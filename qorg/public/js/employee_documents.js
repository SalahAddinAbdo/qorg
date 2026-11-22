frappe.ui.form.on('Employee', {
  refresh(frm) {
    if (frm.is_new()) return;
    frm.add_custom_button(__('Documents and Compliance'), () => {
      frappe.call({method:'qorg.qorg.employee_lifecycle.api.employee_document_compliance',args:{employee:frm.doc.name},freeze:true}).then(r => show_document_compliance(frm,r.message||[]));
    }, __('Employee Lifecycle'));
    frm.add_custom_button(__('New Employee Document'), () => frappe.new_doc('Employee Document Record',{subject_doctype:'Employee',subject_name:frm.doc.name}), __('Employee Lifecycle'));
  }
});
function show_document_compliance(frm, rows) {
  const body=rows.map(x=>`<tr><td>${frappe.utils.escape_html(x.document_type||'')}</td><td>${x.compliant?'<span class="indicator-pill green">'+__('Compliant')+'</span>':'<span class="indicator-pill red">'+__('Missing / Non-compliant')+'</span>'}</td><td>${frappe.utils.escape_html(x.requirement_level||'')}</td><td>${x.record?`<a href="/app/employee-document-record/${encodeURIComponent(x.record)}">${frappe.utils.escape_html(x.record)}</a>`:''}</td></tr>`).join('');
  frappe.msgprint({title:__('Employee Documents and Compliance'),message:`<table class="table table-bordered"><thead><tr><th>${__('Document Type')}</th><th>${__('Status')}</th><th>${__('Requirement')}</th><th>${__('Record')}</th></tr></thead><tbody>${body}</tbody></table>`,wide:true});
}
