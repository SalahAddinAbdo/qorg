frappe.ui.form.on("Workforce Funding Plan", {
  setup(frm) {
    frm.set_query("employee", () => ({ filters: { company: frm.doc.company, status: "Active" } }));
    frm.set_query("supersedes_plan", () => ({ filters: { employee: frm.doc.employee, company: frm.doc.company, docstatus: 1, name: ["!=", frm.doc.name || ""] } }));
    frm.set_query("project", "destinations", () => ({ filters: { company: frm.doc.company, status: ["not in", ["Completed", "Cancelled"]] } }));
    frm.set_query("cost_center", "destinations", () => ({ filters: { company: frm.doc.company, is_group: 0, disabled: 0 } }));
    frm.set_query("funding_agreement", "destinations", (doc, cdt, cdn) => { const row = locals[cdt][cdn]; return { filters: { project: row.project, docstatus: 1 } }; });
    frm.set_query("budget_line", "destinations", (doc, cdt, cdn) => { const row = locals[cdt][cdn]; return { filters: { project: row.project, funding_agreement: row.funding_agreement, is_group: 0 } }; });
  },
  company(frm) { if (!frm.is_new()) return; frm.set_value("employee", null); frm.clear_table("destinations"); frm.refresh_field("destinations"); },
  employee(frm) { if (frm.doc.employee) frm.set_value("supersedes_plan", null); }
});
frappe.ui.form.on("Workforce Funding Destination", {
  project(frm, cdt, cdn) { const row = locals[cdt][cdn]; frappe.model.set_value(cdt, cdn, "funding_agreement", null); frappe.model.set_value(cdt, cdn, "budget_line", null); if (!row.project) return; frappe.db.get_value("Project", row.project, ["company", "cost_center"]).then(r => { if (r.message.company && frm.doc.company !== r.message.company) { frappe.model.set_value(cdt, cdn, "project", null); frappe.throw(__("Project belongs to another company.")); } if (!row.cost_center && r.message.cost_center) frappe.model.set_value(cdt, cdn, "cost_center", r.message.cost_center); }); },
  funding_agreement(frm, cdt, cdn) { frappe.model.set_value(cdt, cdn, "budget_line", null); }
});
