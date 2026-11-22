frappe.ui.form.on('Contract', {
  setup(frm) {
    frm.set_query('qorg_contract_type', () => ({ filters: { is_active: 1 } }));
    frm.set_query('contract_template', () => ({ filters: { qorg_contract_type: frm.doc.qorg_contract_type || '', qorg_is_active: 1, qorg_legal_approval_status: 'Approved' } }));
    frm.set_query('qorg_counterparty_doctype', () => ({ filters: { name: ['not in', ['Customer', 'Supplier', 'Employee']] } }));
    frm.set_query('qorg_project', () => ({ filters: frm.doc.qorg_company ? { company: frm.doc.qorg_company } : {} }));
    frm.set_query('qorg_cost_center', () => ({ filters: frm.doc.qorg_company ? { company: frm.doc.qorg_company, is_group: 0 } : { is_group: 0 } }));
    frm.set_query('qorg_budget_line', () => ({ filters: { company: frm.doc.qorg_company || '', project: frm.doc.qorg_project || '' } }));
    frm.set_query('qorg_award_decision', () => ({ filters: { procurement_process: frm.doc.qorg_procurement_process || '', docstatus: 1 } }));
    frm.set_query('qorg_employee', () => ({ filters: { company: frm.doc.qorg_company || '', status: 'Active' } }));
    frm.set_query('qorg_work_commencement_notice', () => ({ filters: { employee: frm.doc.qorg_employee || '' } }));
    frm.set_query('qorg_participation_engagement', () => ({ filters: { external_person: frm.doc.qorg_external_person || '' } }));
  },
  refresh(frm) {
    set_contract_visibility(frm);
    if (!frm.is_new()) {
      frm.add_custom_button(__('Contract Amendment'), () => frappe.new_doc('Contract Amendment', { contract: frm.doc.name }), __('Create'));
      if (is_procurement(frm.doc.qorg_category)) {
        ['Commitment Ledger','Procure Acceptance'].forEach(dt => frm.add_custom_button(__(dt), () => frappe.call({ method:'qorg.qorg.procurement_contracting.actions.create_or_open_contract_record', args:{ contract_name:frm.doc.name, target_doctype:dt }, freeze:true }).then(r => frappe.set_route('Form',dt,r.message)), __('Create / Open')));
      }
    }
  },
  qorg_contract_type(frm) { apply_type_defaults(frm); },
  contract_template(frm) { apply_template_defaults(frm); },
  qorg_category: set_contract_visibility,
  qorg_party_model: set_contract_visibility,
  qorg_open_ended(frm) { if (frm.doc.qorg_open_ended) frm.set_value('end_date', null); set_contract_visibility(frm); },
  qorg_is_zero_value(frm) {
    if (frm.doc.qorg_is_zero_value) { frm.set_value('qorg_contract_value', 0); frm.set_value('qorg_payment_basis', 'No Payment'); }
    set_contract_visibility(frm);
  },
  qorg_employee(frm) {
    if (frm.doc.qorg_category === 'Employment' && frm.doc.qorg_employee) {
      frm.set_value('party_type', 'Employee'); frm.set_value('party_name', frm.doc.qorg_employee);
    }
  }
});

function blank(v) { return v === undefined || v === null || v === ''; }
function set_if_blank(frm, field, value) { if (blank(frm.doc[field]) && value !== undefined && value !== null && value !== '') frm.set_value(field, value); }
function is_procurement(category) { return ['Procurement','Supply','Service','Works','Consultancy','Framework Agreement'].includes(category); }

function apply_type_defaults(frm) {
  if (!frm.doc.qorg_contract_type) return;
  frappe.db.get_doc('QOrg Contract Type', frm.doc.qorg_contract_type).then(type => {
    frm.set_value('qorg_category', type.category); frm.set_value('qorg_party_model', type.party_model);
    set_if_blank(frm,'contract_template',type.default_contract_template);
    set_if_blank(frm,'party_type',type.default_party_type);
    set_if_blank(frm,'qorg_counterparty_doctype',type.default_extended_party_doctype);
    set_if_blank(frm,'qorg_lifecycle_status',type.initial_lifecycle_status);
    set_if_blank(frm,'qorg_renewal_notice_days',type.renewal_notice_days);
    set_if_blank(frm,'qorg_termination_notice_days',type.termination_notice_days);
    set_if_blank(frm,'qorg_auto_renewal',type.auto_renewal_default);
    if (!frm.doc.qorg_default_values_applied) { frm.set_value('qorg_confidential', type.confidential_by_default || 0); frm.set_value('qorg_auto_renewal', type.auto_renewal_default || 0); }
    frm.set_value('qorg_default_values_applied', 1);
    set_contract_visibility(frm, type);
  });
}

function apply_template_defaults(frm) {
  if (!frm.doc.contract_template || !frm.doc.qorg_contract_type) return;
  frappe.db.get_doc('Contract Template', frm.doc.contract_template).then(t => {
    if (t.qorg_contract_type && t.qorg_contract_type !== frm.doc.qorg_contract_type) {
      frappe.throw(__('The selected template does not belong to this Contract Type.'));
    }
    const map = {qorg_company:'qorg_company',qorg_owning_department:'qorg_owning_department',qorg_contract_manager:'qorg_contract_manager',qorg_legal_owner:'qorg_legal_owner',qorg_confidential:'qorg_confidential',qorg_contract_purpose:'qorg_contract_purpose',qorg_currency:'qorg_currency',qorg_payment_basis:'qorg_payment_basis',qorg_is_zero_value:'qorg_is_zero_value',qorg_advance_payment_percent:'qorg_advance_payment_percent',qorg_retention_percent:'qorg_retention_percent',qorg_liquidated_damages_percent:'qorg_liquidated_damages_percent',qorg_renewal_notice_days:'qorg_renewal_notice_days',qorg_termination_notice_days:'qorg_termination_notice_days',qorg_auto_renewal:'qorg_auto_renewal',qorg_employment_type:'qorg_employment_type',qorg_scope_of_work:'qorg_scope_of_work',qorg_payment_terms:'qorg_payment_terms',qorg_termination_terms:'qorg_termination_terms'};
    Object.entries(map).forEach(([target,source]) => set_if_blank(frm,target,t[source]));
    [['qorg_milestones','qorg_milestones'],['qorg_deliverables','qorg_deliverables'],['qorg_guarantees','qorg_guarantees'],['qorg_required_documents','qorg_required_documents']].forEach(([target,source]) => {
      if (!(frm.doc[target] || []).length && (t[source] || []).length) { frm.clear_table(target); t[source].forEach(row => { const child=frm.add_child(target); Object.keys(row).filter(k => !['name','parent','parenttype','parentfield','idx','doctype','creation','modified','modified_by','owner','docstatus'].includes(k)).forEach(k => child[k]=row[k]); }); frm.refresh_field(target); }
    });
    frm.set_value('qorg_default_values_applied', 1);
    set_contract_visibility(frm);
  });
}

function set_contract_visibility(frm) {
  const category=frm.doc.qorg_category, model=frm.doc.qorg_party_model, financial=!frm.doc.qorg_is_zero_value;
  frm.toggle_display('qorg_counterparty_section',['Extended Party','Either Standard or Extended'].includes(model));
  frm.toggle_display('qorg_contract_parties',model==='Multiple Parties');
  frm.toggle_display('party_type',['Standard Party','Either Standard or Extended'].includes(model));
  frm.toggle_display('party_name',['Standard Party','Either Standard or Extended'].includes(model));
  frm.toggle_display('qorg_employment_section',category==='Employment');
  frm.toggle_display('qorg_participation_section',['Volunteer','Internship'].includes(category));
  ['qorg_currency','qorg_contract_value','qorg_ceiling_amount','qorg_payment_basis','qorg_funding_agreement','qorg_budget_line','qorg_advance_payment_percent','qorg_retention_percent','qorg_liquidated_damages_percent'].forEach(f=>frm.toggle_display(f,financial));
  ['qorg_procurement_process','qorg_award_decision','qorg_technical_manager','qorg_warranty_end_date','qorg_defects_liability_end_date','qorg_milestones','qorg_guarantees'].forEach(f=>frm.toggle_display(f,is_procurement(category)));
  frm.toggle_reqd('end_date',!frm.doc.qorg_open_ended);
}
