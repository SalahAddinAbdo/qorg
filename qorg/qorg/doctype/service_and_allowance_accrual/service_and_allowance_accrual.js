frappe.ui.form.on("Service and Allowance Accrual", {
 refresh(frm) {
  frm.dashboard.set_headline_alert(__("Legacy record. Use Service Allowance Accrual for new transactions."), "orange");
  if (frm.is_new()) frappe.throw(__("This legacy DocType is closed for new transactions. Use Service Allowance Accrual."));
 }
});
