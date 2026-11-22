frappe.ui.form.on('QOrg Contract Type', {
  setup(frm) {
    frm.set_query('default_party_type', () => ({ filters: { name: ['in', ['Customer', 'Supplier', 'Employee']] } }));
    frm.set_query('default_extended_party_doctype', () => ({ filters: { name: ['not in', ['Customer', 'Supplier', 'Employee']] } }));
    frm.set_query('default_contract_template', () => ({ filters: { qorg_is_active: 1, qorg_contract_type: frm.doc.name || '' } }));
    frm.set_query('default_print_format', () => ({ filters: { doc_type: 'Contract', disabled: 0 } }));
    frm.set_query('party_doctype', 'allowed_parties', (doc, cdt, cdn) => {
      const row = locals[cdt][cdn];
      return row.party_mode === 'Standard'
        ? { filters: { name: ['in', ['Customer', 'Supplier', 'Employee']] } }
        : { filters: { name: ['not in', ['Customer', 'Supplier', 'Employee']] } };
    });
  },
  refresh: refresh_policy,
  party_model: refresh_policy,
  category: refresh_policy
});

frappe.ui.form.on('QOrg Contract Allowed Party', {
  party_mode(frm, cdt, cdn) {
    frappe.model.set_value(cdt, cdn, 'party_doctype', '');
  },
  is_default(frm, cdt, cdn) {
    const row = locals[cdt][cdn];
    if (!row.is_default) return;
    (frm.doc.allowed_parties || []).forEach(other => {
      if (other.name !== row.name) frappe.model.set_value(other.doctype, other.name, 'is_default', 0);
    });
  }
});

function refresh_policy(frm) {
  const no_party = frm.doc.party_model === 'No Counterparty';
  frm.toggle_display('allowed_parties', !no_party);
  frm.toggle_reqd('allowed_parties', !no_party);
  frm.toggle_display('hr_section', ['Employment', 'Volunteer', 'Internship', 'Consultancy'].includes(frm.doc.category));
  if (frm.doc.party_model === 'Multiple Parties') frm.set_value('allow_multiple_parties', 1);
}
