frappe.ui.form.on('Contract', {
  setup(frm) {
    frm.set_query('qorg_contract_type', () => ({ filters: { is_active: 1 } }));
    frm.set_query('contract_template', () => ({
      filters: frm.doc.qorg_contract_type ? { qorg_contract_type: frm.doc.qorg_contract_type, qorg_is_active: 1 } : { qorg_is_active: 1 }
    }));
    frm.set_query('qorg_counterparty_doctype', () => ({
      filters: { name: ['not in', ['Customer', 'Supplier', 'Employee']] }
    }));
  },
  refresh(frm) {
    if (!frm.is_new()) {
      if (['Procurement','Supply','Service','Works','Consultancy','Framework Agreement'].includes(frm.doc.qorg_category)) {
        ['Commitment Ledger','Procure Acceptance','Contract Amendment'].forEach(dt => frm.add_custom_button(__(dt), () => frappe.call({method:'qorg.qorg.procurement_contracting.actions.create_or_open_contract_record', args:{contract_name:frm.doc.name,target_doctype:dt}, freeze:true}).then(r => frappe.set_route('Form',dt,r.message)), __('Create / Open')));
      }
      frm.add_custom_button(__('Contract Amendment'), () => {
        frappe.new_doc('Contract Amendment', { contract: frm.doc.name });
      }, __('Create'));
    }
    set_contract_visibility(frm);
  },
  qorg_contract_type(frm) {
    if (!frm.doc.qorg_contract_type) return;
    frappe.db.get_value('QOrg Contract Type', frm.doc.qorg_contract_type,
      ['category', 'default_party_type', 'default_contract_template', 'confidential_by_default', 'renewal_notice_days', 'termination_notice_days'])
      .then(({ message }) => {
        if (!message) return;
        frm.set_value('qorg_category', message.category);
        if (!frm.doc.party_name && message.default_party_type) frm.set_value('party_type', message.default_party_type);
        if (!frm.doc.contract_template && message.default_contract_template) frm.set_value('contract_template', message.default_contract_template);
        if (message.confidential_by_default) frm.set_value('qorg_confidential', 1);
        if (!frm.doc.qorg_renewal_notice_days) frm.set_value('qorg_renewal_notice_days', message.renewal_notice_days);
        if (!frm.doc.qorg_termination_notice_days) frm.set_value('qorg_termination_notice_days', message.termination_notice_days);
        set_contract_visibility(frm);
      });
  },
  qorg_category: set_contract_visibility,
  qorg_is_zero_value(frm) {
    if (frm.doc.qorg_is_zero_value) {
      frm.set_value('qorg_contract_value', 0);
      frm.set_value('qorg_payment_basis', 'No Payment');
    }
  },
  qorg_employee(frm) {
    if (frm.doc.qorg_category === 'Employment' && frm.doc.qorg_employee) {
      frm.set_value('party_type', 'Employee');
      frm.set_value('party_name', frm.doc.qorg_employee);
    }
  }
});

function set_contract_visibility(frm) {
  const category = frm.doc.qorg_category;
  frm.toggle_display('qorg_employment_section', category === 'Employment');
  frm.toggle_display('qorg_participation_section', ['Volunteer', 'Internship'].includes(category));
  frm.toggle_display('qorg_procurement_process', ['Procurement', 'Supply', 'Service', 'Works', 'Consultancy', 'Framework Agreement'].includes(category));
  frm.toggle_display('qorg_award_decision', ['Procurement', 'Supply', 'Service', 'Works', 'Consultancy', 'Framework Agreement'].includes(category));
}
