frappe.ui.form.on("Request for Quotation", {
  custom_contact_employee(frm) {
    if (!frm.doc.custom_contact_employee) return;
    frappe.db.get_value("Employee", frm.doc.custom_contact_employee, ["employee_name","designation","cell_number","company_email","personal_email","user_id"]).then(({message}) => {
      if (!message) return;
      frm.set_value("custom_contact_name", message.employee_name || "");
      frm.set_value("custom_contact_designation", message.designation || "");
      frm.set_value("custom_contact_phone", message.cell_number || "");
      frm.set_value("custom_contact_email", message.company_email || message.personal_email || message.user_id || "");
    });
  }
});
