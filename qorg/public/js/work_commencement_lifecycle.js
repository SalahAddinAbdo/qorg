frappe.ui.form.on('Work Commencement Notice', {
  refresh(frm) {
    if (frm.doc.docstatus === 0 && frm.doc.status === 'Commenced' && !frm.is_new()) {
      frm.add_custom_button(__('Prepare Employee Lifecycle'), () => {
        frappe.call({
          method: 'qorg.qorg.employee_lifecycle.api.prepare_from_commencement',
          args: { name: frm.doc.name },
          freeze: true,
          freeze_message: __('Creating or linking Employee, Employment Contract and Onboarding...')
        }).then(r => {
          const result = r.message || {};
          const created = (result.created || []).join(', ') || __('No new records; existing records were linked.');
          frappe.msgprint({ title: __('Employee Lifecycle Prepared'), message: __('Created: {0}', [created]), indicator: 'green' });
          frm.reload_doc();
        });
      }, __('Actions'));
    }
  },
  employee(frm) {
    if (frm.doc.employee) {
      frm.set_intro(__('An existing Employee is selected. The server will validate that it matches the approved commencement before submission.'), 'blue');
    }
  }
});
