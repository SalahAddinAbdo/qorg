frappe.ui.form.on("Monthly Effort Certification", {
  setup(frm) {
    frm.set_query("employee", () => ({ filters: { company: frm.doc.company, status: "Active" } }));
    frm.set_query("project", "details", () => ({ filters: { company: frm.doc.company, status: ["not in", ["Completed", "Cancelled"]] } }));
    frm.set_query("cost_center", "details", () => ({ filters: { company: frm.doc.company, is_group: 0, disabled: 0 } }));
    frm.set_query("funding_agreement", "details", (doc, cdt, cdn) => { const row = locals[cdt][cdn]; return { filters: { project: row.project, docstatus: 1 } }; });
    frm.set_query("budget_line", "details", (doc, cdt, cdn) => { const row = locals[cdt][cdn]; return { filters: { project: row.project, funding_agreement: row.funding_agreement, is_group: 0 } }; });
  },
  refresh(frm) { if (frm.doc.docstatus !== 0) return; const actions = { "Draft": "Employee Certify", "Employee Certified": "Supervisor Approve", "Supervisor Approved": "Finance Verify" }; const action = actions[frm.doc.status]; if (action) frm.add_custom_button(__(action), () => frappe.call({ method: "qorg.qorg.payroll_workforce_allocation.effort.certify_effort", args: { name: frm.doc.name, action }, freeze: true, callback: () => frm.reload_doc() }), __("Certification")); }
});
frappe.ui.form.on("Monthly Effort Certification Detail", {
  project(frm, cdt, cdn) { frappe.model.set_value(cdt, cdn, "funding_agreement", null); frappe.model.set_value(cdt, cdn, "budget_line", null); },
  funding_agreement(frm, cdt, cdn) { frappe.model.set_value(cdt, cdn, "budget_line", null); }
});
