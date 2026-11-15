(() => {
  const get_project = (frm, cdt, cdn) => {
    if (cdt && cdn) {
      const row = locals[cdt] && locals[cdt][cdn];
      return row && (row.project || frm.doc.project);
    }
    return frm.doc.project;
  };

  const agreement_filters = (frm, cdt, cdn) => {
    const row = locals[cdt] && locals[cdt][cdn];
    const filters = { docstatus: 1, status: ["in", ["Active", "Closing"]] };
    const project = get_project(frm, cdt, cdn);
    if (project) filters.project = project;
    if (row && row.donor) filters.donor = row.donor;
    return { filters };
  };

  frappe.ui.form.on("Project", {
    setup(frm) {
      frm.set_query("funding_agreement", "custom_funding_sources", (doc, cdt, cdn) => agreement_filters(frm, cdt, cdn));
    }
  });

  frappe.ui.form.on("Project Funding Source", {
    donor(frm, cdt, cdn) {
      frappe.model.set_value(cdt, cdn, "funding_agreement", null);
    },
    funding_agreement(frm, cdt, cdn) {
      const row = locals[cdt][cdn];
      if (!row.funding_agreement) return;
      frappe.db.get_value("Funding Agreement", row.funding_agreement, [
        "donor", "agreement_reference", "agreement_currency", "agreement_amount", "exchange_rate",
        "start_date", "end_date", "eligibility_start_date", "eligibility_end_date", "flexibility_percent"
      ]).then(({ message: v }) => {
        if (!v) return;
        const values = {
          donor: v.donor, agreement_reference: v.agreement_reference, donor_currency: v.agreement_currency,
          approved_amount_donor_currency: v.agreement_amount, exchange_rate: v.exchange_rate,
          funding_start_date: v.start_date, funding_end_date: v.end_date,
          eligibility_start_date: v.eligibility_start_date, eligibility_end_date: v.eligibility_end_date,
          flexibility_percent: v.flexibility_percent
        };
        Object.entries(values).forEach(([key, value]) => frappe.model.set_value(cdt, cdn, key, value));
      });
    }
  });

  frappe.ui.form.on("Project Change Request", {
    setup(frm) {
      const query = (doc, cdt, cdn) => {
        const row = locals[cdt][cdn];
        const filters = { project: frm.doc.project, is_group: 0 };
        if (frm.doc.funding_agreement) filters.funding_agreement = frm.doc.funding_agreement;
        return { filters };
      };
      frm.set_query("source_budget_line", "budget_transfer_rows", query);
      frm.set_query("target_budget_line", "budget_transfer_rows", (doc, cdt, cdn) => {
        const q = query(doc, cdt, cdn); const row = locals[cdt][cdn];
        if (row.source_budget_line) q.filters.name = ["!=", row.source_budget_line];
        return q;
      });
    }
  });

  frappe.ui.form.on("Budget Transfer Item", {
    source_budget_line(frm, cdt, cdn) {
      const row = locals[cdt][cdn];
      if (row.target_budget_line === row.source_budget_line) frappe.model.set_value(cdt, cdn, "target_budget_line", null);
    }
  });


})();
