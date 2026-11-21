frappe.ui.form.on('Award Decision', {
  refresh(frm) {
    if (frm.is_new()) return;
    if (frm.doc.decision === 'Approved') {
      frm.add_custom_button(__('Contract'), () => {
        frappe.call({
          method: 'qorg.qorg.procurement_contracting.actions.create_or_open_contract',
          args: { award_decision: frm.doc.name }, freeze: true
        }).then(({ message }) => {
          if (message.existing) return frappe.set_route('Form', 'Contract', message.existing);
          frappe.new_doc('Contract', message.defaults || {});
        });
      }, __('Create / Open'));
    }
    frm.add_custom_button(__('Preview Award Notification'), () => qorg.procurement.preview_and_send(frm, 'Award Notification', ''), __('Communication'));
    frm.add_custom_button(__('Preview Unsuccessful Notice'), () => qorg.procurement.preview_and_send(frm, 'Unsuccessful Bidder Notice', ''), __('Communication'));
  }
});
