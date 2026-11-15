frappe.ui.form.on("Budget Line", {
  project(frm) { qorg_apply_finance_defaults(frm); },
  funding_agreement(frm) { qorg_apply_finance_defaults(frm); },
  cost_category(frm) { qorg_mark_finance_override(frm); },
  allow_budget_transfer(frm) { qorg_mark_finance_override(frm); },
  flexibility_percent(frm) { qorg_mark_finance_override(frm); },
  eligibility_start_date(frm) { qorg_mark_finance_override(frm); },
  eligibility_end_date(frm) { qorg_mark_finance_override(frm); }
});
function qorg_mark_finance_override(frm) {
  if (!frm.__qorg_applying_finance_defaults && !frm.is_new()) frm.set_value("finance_values_overridden", 1);
}
function qorg_apply_finance_defaults(frm) {
  if (!frm.doc.project || frm.doc.finance_values_overridden) return;
  frappe.call({method:"qorg.qorg.finance_budget_grants.services.get_budget_line_finance_defaults",args:{project:frm.doc.project,funding_agreement:frm.doc.funding_agreement},callback(r){
    const values=r.message||{}; frm.__qorg_applying_finance_defaults=true;
    Promise.all(Object.entries(values).map(([f,v])=>frm.set_value(f,v))).finally(()=>{frm.__qorg_applying_finance_defaults=false;});
  }});
}

// v1.5.0: simplified, contextual finance forms. Functional fields remain available
// to server logic and audit records; only non-actionable fields are hidden from operators.
(function () {
  const toggle = (frm, field, visible) => {
    if (frm.fields_dict[field]) frm.toggle_display(field, Boolean(visible));
  };

  frappe.ui.form.on("Project Change Request", {
    refresh(frm) {
      const transfer = Boolean(frm.doc.budget_transfer_required);
      ["funding_agreement", "budget_transfer_rows"].forEach((f) => toggle(frm, f, transfer));
      ["budget_transfer_amount", "donor_approval_required", "donor_approval_reference"]
        .forEach((f) => toggle(frm, f, transfer));
      const needsDonor = transfer && Boolean(frm.doc.donor_approval_required);
      ["donor_approval_status", "donor_reference", "donor_approval_attachment"]
        .forEach((f) => toggle(frm, f, needsDonor));
      const applied = Boolean(frm.doc.budget_transfer_audit || frm.doc.budget_transfer_applied_on || frm.doc.change_applied);
      ["budget_transfer_applied_on", "budget_transfer_applied_by", "budget_transfer_audit"]
        .forEach((f) => toggle(frm, f, applied));
      if (frm.fields_dict.budget_transfer_amount) {
        frm.set_df_property("budget_transfer_amount", "read_only", 1);
      }
      if (frm.fields_dict.donor_approval_required) {
        frm.set_df_property("donor_approval_required", "read_only", 1);
      }
    },
    budget_transfer_required(frm) { frm.trigger("refresh"); },
    donor_approval_required(frm) { frm.trigger("refresh"); },
    budget_transfer_rows_add(frm) { frm.trigger("refresh"); },
    budget_transfer_rows_remove(frm) { frm.trigger("refresh"); }
  });

  frappe.ui.form.on("Budget Line", {
    refresh(frm) {
      ["finance_values_overridden", "source_funding_row"].forEach((f) => toggle(frm, f, false));
      ["current_approved_amount"].forEach((f) => toggle(frm, f, true));
    }
  });
})();

