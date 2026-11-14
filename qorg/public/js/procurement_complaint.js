frappe.ui.form.on("Procurement Complaint", {
  refresh(frm) {
    if (frm.is_new() || !frappe.user.has_role(["Procurement Manager", "System Manager"])) return;
    frm.add_custom_button(__("Preview or Send Acknowledgement"), () => {
      const dialog = new frappe.ui.Dialog({
        title: __("Complaint Acknowledgement"),
        fields: [
          {fieldname: "recipients", label: __("Recipients"), fieldtype: "Data", options: "Email", reqd: 1},
          {fieldname: "cc", label: __("CC"), fieldtype: "Data", description: __("Comma-separated email addresses")},
          {fieldname: "preview", label: __("Preview"), fieldtype: "HTML"}
        ],
        primary_action_label: __("Send"),
        primary_action(values) {
          frappe.call({
            method: "qorg.qorg.procurement_contracting.communications.send_template",
            type: "POST",
            freeze: true,
            args: {
              reference_doctype: frm.doctype,
              reference_name: frm.doc.name,
              template_name: "Procurement Complaint Acknowledgement",
              recipients: values.recipients,
              cc: values.cc
            },
            callback() { dialog.hide(); frm.reload_doc(); }
          });
        }
      });
      dialog.show();
      dialog.fields_dict.recipients.$input.on("change", () => {
        if (!dialog.get_value("recipients")) return;
        frappe.call({
          method: "qorg.qorg.procurement_contracting.communications.preview_template",
          args: {reference_doctype: frm.doctype, reference_name: frm.doc.name, template_name: "Procurement Complaint Acknowledgement"},
          callback(r) {
            const message = r.message || {};
            dialog.fields_dict.preview.$wrapper.html(`<div class="qorg-message-preview"><h5>${frappe.utils.escape_html(message.subject || "")}</h5>${message.message || ""}</div>`);
          }
        });
      });
    }, __("Communications"));
  }
});
