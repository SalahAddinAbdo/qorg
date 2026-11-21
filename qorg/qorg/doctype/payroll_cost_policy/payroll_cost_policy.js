frappe.ui.form.on("Payroll Cost Policy", {
  setup(frm) {
    frm.set_query("funding_agreement", () => ({ filters: { company: frm.doc.company, docstatus: 1 } }));
    frm.set_query("supersedes_policy", () => ({ filters: { company: frm.doc.company, docstatus: 1, name: ["!=", frm.doc.name || ""] } }));
    frm.set_query("fallback_project", "component_rules", () => ({ filters: { company: frm.doc.company, status: ["not in", ["Completed", "Cancelled"]] } }));
    frm.set_query("fallback_funding_agreement", "component_rules", (doc, cdt, cdn) => { const row = locals[cdt][cdn]; return { filters: { project: row.fallback_project, docstatus: 1 } }; });
    frm.set_query("fallback_budget_line", "component_rules", (doc, cdt, cdn) => { const row = locals[cdt][cdn]; return { filters: { project: row.fallback_project, funding_agreement: row.fallback_funding_agreement, is_group: 0 } }; });
    frm.set_query("liability_account", "liability_rules", () => ({ filters: { company: frm.doc.company, is_group: 0, disabled: 0, account_type: ["in", ["Payable", "Tax"]] } }));
  }
});
frappe.ui.form.on("Payroll Component Rule", {
  salary_component(frm, cdt, cdn) { const row = locals[cdt][cdn]; if (!row.salary_component) return; frappe.db.get_value("Salary Component", row.salary_component, ["type", "is_statistical_component", "do_not_include_in_total"]).then(r => { if ((r.message.is_statistical_component || r.message.do_not_include_in_total) && !row.cost_treatment) frappe.model.set_value(cdt, cdn, "cost_treatment", "Informational"); }); },
  fallback_project(frm, cdt, cdn) { frappe.model.set_value(cdt, cdn, "fallback_funding_agreement", null); frappe.model.set_value(cdt, cdn, "fallback_budget_line", null); },
  fallback_funding_agreement(frm, cdt, cdn) { frappe.model.set_value(cdt, cdn, "fallback_budget_line", null); }
});
