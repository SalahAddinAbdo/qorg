function recalculate_handover_row(frm, cdt, cdn) {
  const row = locals[cdt][cdn];
  const delivered = flt(row.delivered_qty);
  const received = flt(row.received_qty);
  const rejected = flt(row.rejected_qty);
  const damaged = flt(row.damaged_qty);
  const accepted = Math.max(received - rejected - damaged, 0);
  const short = Math.max(delivered - received, 0);
  frappe.model.set_value(cdt, cdn, "accepted_qty", accepted);
  frappe.model.set_value(cdt, cdn, "short_qty", short);
}

frappe.ui.form.on("Stock Handover", {
  refresh(frm) {
    if (!frm.is_new() && frm.doc.docstatus < 2 && frm.doc.recipient_type !== "Employee" && frm.doc.external_recipient_email) {
      frm.add_custom_button(__("Send Acknowledgement Email"), () => {
        frappe.call({
          method: "qorg.qorg.inventory_asset_custody.actions.send_handover_email",
          args: { name: frm.doc.name },
          freeze: true,
          callback: () => frappe.show_alert({ message: __("Email queued"), indicator: "green" })
        });
      }, __("Communication"));
    }
    if (frm.doc.discrepancy_status === "Open") {
      frm.add_custom_button(__("Create Incident"), () => {
        frappe.call({
          method: "qorg.qorg.inventory_asset_custody.actions.make_incident",
          args: { source_doctype: frm.doc.doctype, source_name: frm.doc.name },
          callback: (r) => {
            if (!r.message) return;
            frappe.model.sync(r.message);
            frappe.set_route("Form", "Asset Incident", r.message.name);
          }
        });
      }, __("Create"));
    }
  },

  recipient_type(frm) {
    if (frm.doc.recipient_type === "Employee") {
      frm.set_value("recipient_external_person", null);
      frm.set_value("recipient_partner", null);
      frm.set_value("recipient_supplier", null);
      frm.set_value("recipient_transporter", null);
    } else {
      frm.set_value("recipient_employee", null);
      frm.set_value("recipient_user", null);
    }
  },

  recipient_employee(frm) {
    if (!frm.doc.recipient_employee) return;
    frappe.db.get_value("Employee", frm.doc.recipient_employee, ["user_id", "employee_name", "cell_number", "company_email", "personal_email"]).then(({ message }) => {
      if (!message) return;
      frm.set_value("recipient_user", message.user_id || null);
    });
  },

  issue_usage_type(frm) {
    if (frm.doc.issue_usage_type === "Temporary Issue") {
      frm.set_value("return_expected", 1);
    }
    if (!["Employee Custody", "Temporary Issue"].includes(frm.doc.issue_usage_type)) {
      frm.set_value("return_expected", 0);
      frm.set_value("expected_return_date", null);
    }
  },

  return_expected(frm) {
    if (!frm.doc.return_expected) frm.set_value("expected_return_date", null);
  },

  delivery_method(frm) {
    if (frm.doc.delivery_method === "Recipient Pickup") {
      ["transport_provider", "driver_name", "driver_phone", "vehicle_type", "vehicle_number", "waybill_number"].forEach((fieldname) => frm.set_value(fieldname, null));
    }
  }
});

frappe.ui.form.on("Stock Handover Item", {
  delivered_qty: recalculate_handover_row,
  received_qty: recalculate_handover_row,
  rejected_qty: recalculate_handover_row,
  damaged_qty: recalculate_handover_row
});
