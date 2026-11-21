frappe.ui.form.on('Contract Template', {
  setup(frm) {
    frm.set_query('qorg_contract_type', () => ({ filters: { is_active: 1 } }));
  },
  refresh(frm) {
    if (frm.doc.qorg_legal_approval_status === 'Approved') {
      frm.set_intro(__('Approved templates are versioned references. Create a new template version instead of overwriting legal text.'), 'blue');
    }
  }
});
