frappe.ui.form.on("Payroll Allocation Run", {
  setup(frm) { frm.set_query("payroll_entry", () => ({ filters: { company: frm.doc.company, docstatus: 1 } })); },
  company(frm) { if (frm.is_new()) frm.set_value("payroll_entry", null); },
  refresh(frm) {
    const call = method => frappe.call({ method: `qorg.qorg.payroll_workforce_allocation.lifecycle.${method}`, args: { run_name: frm.doc.name }, freeze: true, callback: () => frm.reload_doc() });
    if (frm.is_new()) return;
    if (["Draft", "Calculated", "Exceptions Found", "Ready for Approval"].includes(frm.doc.status)) frm.add_custom_button(__("Calculate Allocation"), () => call("calculate"), __("Payroll Allocation"));
    if (frm.doc.status === "Ready for Approval") frm.add_custom_button(__("Approve Allocation"), () => call("approve"), __("Payroll Allocation"));
    if (frm.doc.status === "Approved") frm.add_custom_button(__("Post Allocation"), () => call("post"), __("Payroll Allocation"));
    if (frm.doc.status === "Posted") frm.add_custom_button(__("Reconcile"), () => call("reconcile"), __("Payroll Allocation"));
    if (frm.doc.status === "Reconciled") frm.add_custom_button(__("Close"), () => call("close"), __("Payroll Allocation"));
    if (["Posted", "Reconciled", "Closed"].includes(frm.doc.status)) frm.add_custom_button(__("Reverse Allocation"), () => call("reverse"), __("Payroll Allocation"));
  }
});
