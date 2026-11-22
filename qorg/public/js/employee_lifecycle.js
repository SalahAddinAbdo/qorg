frappe.ui.form.on('Employee', {
  refresh(frm) {
    if (frm.is_new()) return;
    frm.add_custom_button(__('Evaluate Service Readiness'), () => {
      frappe.call({
        method: 'qorg.qorg.employee_lifecycle.api.evaluate_readiness',
        args: { employee: frm.doc.name },
        freeze: true,
        freeze_message: __('Evaluating employment, payroll, attendance and leave readiness...')
      }).then(r => {
        const data = r.message || {};
        show_readiness(data);
        frm.reload_doc();
      });
    }, __('Employee Lifecycle'));
    frm.add_custom_button(__('Activate Ready Services'), () => {
      frappe.prompt([
        { fieldname:'services', label:__('Services'), fieldtype:'MultiSelectPills', options:[
          {label:__('Employment'),value:'employment'}, {label:__('Payroll'),value:'payroll'},
          {label:__('Attendance'),value:'attendance'}, {label:__('Leave'),value:'leave'}
        ], reqd:1 }
      ], values => {
        const services = (values.services || []).map(v => typeof v === 'string' ? v : v.value);
        frappe.call({ method:'qorg.qorg.employee_lifecycle.api.activate_services', args:{ employee:frm.doc.name, services:JSON.stringify(services) }, freeze:true }).then(r => {
          frappe.msgprint({title:__('Services Activated'),message:__('Activated: {0}',[(r.message.activated || []).join(', ')]),indicator:'green'});
          frm.reload_doc();
        });
      }, __('Activate Employee Services'));
    }, __('Employee Lifecycle'));
  }
});

function show_readiness(data) {
  const rows = Object.entries(data.services || {}).map(([name, row]) => {
    const indicator = row.ready ? 'green' : 'red';
    const details = row.ready ? __('Ready') : (row.blockers || []).join('<br>');
    return `<tr><td>${frappe.utils.escape_html(__(name))}</td><td><span class="indicator-pill ${indicator}">${frappe.utils.escape_html(details)}</span></td><td>${frappe.utils.escape_html(row.effective_date || '')}</td></tr>`;
  }).join('');
  frappe.msgprint({title:__('Service Readiness: {0}',[data.overall_status || '']),message:`<table class="table table-bordered"><thead><tr><th>${__('Service')}</th><th>${__('Result')}</th><th>${__('Effective Date')}</th></tr></thead><tbody>${rows}</tbody></table>`,wide:true});
}
