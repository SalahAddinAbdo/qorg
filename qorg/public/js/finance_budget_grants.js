const QORG_BUDGET_LINE_INHERITED_FIELDS = [
  "project_funding_source_row",
  "source_donor",
  "funding_agreement",
  "cost_category",
  "allow_budget_transfer",
  "flexibility_percent",
  "eligibility_start_date",
  "eligibility_end_date"
];

frappe.ui.form.on("Budget Line", {
  async project(frm) {
    frm.__qorg_finance_request = (frm.__qorg_finance_request || 0) + 1;
    frm.__qorg_applying_finance_defaults = true;
    try {
      if (frm.fields_dict.finance_values_overridden) {
        await frm.set_value("finance_values_overridden", 0);
      }
      for (const fieldname of QORG_BUDGET_LINE_INHERITED_FIELDS) {
        if (frm.fields_dict[fieldname] && frm.doc[fieldname]) {
          await frm.set_value(fieldname, null);
        }
      }
    } finally {
      frm.__qorg_applying_finance_defaults = false;
    }
    await qorg_apply_finance_defaults(frm, { force: true });
  },

  async funding_agreement(frm) {
    if (!frm.__qorg_applying_finance_defaults) {
      await qorg_apply_finance_defaults(frm, { force: true });
    }
  },

  cost_category(frm) { qorg_mark_finance_override(frm); },
  allow_budget_transfer(frm) { qorg_mark_finance_override(frm); },
  flexibility_percent(frm) { qorg_mark_finance_override(frm); },
  eligibility_start_date(frm) { qorg_mark_finance_override(frm); },
  eligibility_end_date(frm) { qorg_mark_finance_override(frm); }
});

function qorg_mark_finance_override(frm) {
  if (!frm.__qorg_applying_finance_defaults && !frm.is_new()) {
    frm.set_value("finance_values_overridden", 1);
  }
}

async function qorg_apply_finance_defaults(frm, options = {}) {
  if (!frm.doc.project || (!options.force && frm.doc.finance_values_overridden)) return;

  const project = frm.doc.project;
  const agreement = frm.doc.funding_agreement || null;
  const requestId = (frm.__qorg_finance_request || 0) + 1;
  frm.__qorg_finance_request = requestId;

  const response = await frappe.call({
    method: "qorg.qorg.finance_budget_grants.services.get_budget_line_finance_defaults",
    args: { project, funding_agreement: agreement },
    freeze: false
  });

  if (requestId !== frm.__qorg_finance_request || project !== frm.doc.project) return;
  const values = response.message || {};
  if (!Object.keys(values).length) return;

  frm.__qorg_applying_finance_defaults = true;
  try {
    for (const fieldname of QORG_BUDGET_LINE_INHERITED_FIELDS) {
      if (frm.fields_dict[fieldname] && Object.prototype.hasOwnProperty.call(values, fieldname)) {
        await frm.set_value(fieldname, values[fieldname]);
      }
    }
  } finally {
    frm.__qorg_applying_finance_defaults = false;
  }
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

