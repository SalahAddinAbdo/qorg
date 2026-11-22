frappe.ui.form.on('Contract Template', {
  setup(frm) {
    frm.set_query('qorg_contract_type', () => ({ filters: { is_active: 1 } }));
    frm.set_query('qorg_owning_department', () => ({ filters: frm.doc.qorg_company ? { company: frm.doc.qorg_company } : {} }));
    frm.set_query('qorg_default_party_doctype', () => ({ filters: { name: ['not in', ['Customer', 'Supplier', 'Employee']] } }));
  },
  refresh(frm) {
    set_template_visibility(frm);
    if (frm.doc.qorg_legal_approval_status === 'Approved') {
      frm.set_intro(__('Approved templates are versioned references. Create a new version instead of overwriting approved legal content.'), 'blue');
    }
  },
  qorg_contract_type(frm) {
    if (!frm.doc.qorg_contract_type) return;
    frappe.db.get_doc('QOrg Contract Type', frm.doc.qorg_contract_type).then(type => {
      frm.set_value('qorg_category', type.category);
      set_if_blank(frm, 'qorg_language', type.default_language);
      set_if_blank(frm, 'qorg_default_duration_months', type.default_duration_months);
      set_if_blank(frm, 'qorg_allow_open_ended', type.allows_open_ended_period);
      set_if_blank(frm, 'qorg_auto_renewal', type.auto_renewal_default);
      set_if_blank(frm, 'qorg_renewal_notice_days', type.renewal_notice_days);
      set_if_blank(frm, 'qorg_termination_notice_days', type.termination_notice_days);
      set_if_blank(frm, 'qorg_confidential', type.confidential_by_default);
      set_template_visibility(frm);
    });
  },
  qorg_is_zero_value: set_template_visibility,
  qorg_category: set_template_visibility
});

function set_if_blank(frm, field, value) {
  if ((frm.doc[field] === undefined || frm.doc[field] === null || frm.doc[field] === '') && value !== undefined && value !== null) frm.set_value(field, value);
}

function set_template_visibility(frm) {
  const category = frm.doc.qorg_category;
  const procurement = ['Procurement','Supply','Service','Works','Consultancy','Framework Agreement'].includes(category);
  const financial = !frm.doc.qorg_is_zero_value;
  frm.toggle_display('qorg_employment_section', category === 'Employment');
  frm.toggle_display('qorg_participation_section', ['Volunteer','Internship'].includes(category));
  ['qorg_currency','qorg_payment_basis','qorg_advance_payment_percent','qorg_retention_percent','qorg_liquidated_damages_percent','qorg_ceiling_policy'].forEach(f => frm.toggle_display(f, financial));
  ['qorg_milestones','qorg_guarantees'].forEach(f => frm.toggle_display(f, procurement));
}
