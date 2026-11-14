(() => {
  const CONFIG = {
    "Participation Application": [
      ["Application Received", "Participation - Application Received - Bilingual"],
      ["Screening Outcome", "Participation - Screening Outcome - Bilingual"],
      ["Assessment Invitation", "Participation - Assessment Invitation - Bilingual"],
      ["Selection Notice", "Participation - Selection Notice - Bilingual"],
      ["Reserve Notice", "Participation - Reserve Notice - Bilingual"],
      ["Application Not Selected", "Participation - Application Not Selected - Bilingual"]
    ],
    "Participation Engagement": [
      ["Agreement Issued", "Participation - Agreement Issued - Bilingual"],
      ["Onboarding Reminder", "Participation - Onboarding Reminder - Bilingual"],
      ["Completion Notice", "Participation - Completion Notice - Bilingual"],
      ["Exit Notice", "Participation - Exit Notice - Bilingual"],
      ["Renewal Notice", "Participation - Renewal Notice - Bilingual"]
    ],
    "Participation Service Log": [["Service Log Verification", "Participation - Service Log Verification - Bilingual"]],
    "Participation Certificate": [["Certificate Issued", "Participation - Certificate Issued - Bilingual"]]
  };

  function defaultRecipient(frm) {
    return frm.doc.email || frm.doc.primary_email || frm.doc.email_id || "";
  }

  function openCommunication(frm) {
    const choices = CONFIG[frm.doctype] || [];
    const labels = choices.map((row) => row[0]);
    const dialog = new frappe.ui.Dialog({
      title: __("Participation Communication"),
      fields: [
        {fieldname: "notification_type", label: __("Communication Type"), fieldtype: "Select", options: labels.join("\n"), reqd: 1},
        {fieldname: "primary_recipient", label: __("Primary Recipient"), fieldtype: "Data", options: "Email", default: defaultRecipient(frm), reqd: 1},
        {fieldname: "cc", label: __("CC"), fieldtype: "Data", description: __("Comma-separated email addresses")},
        {fieldname: "preview", label: __("Preview"), fieldtype: "HTML"}
      ],
      primary_action_label: __("Send"),
      primary_action(values) {
        const match = choices.find((row) => row[0] === values.notification_type);
        if (!match) return;
        frappe.call({
          method: "qorg.qorg.volunteer_management.api.send_notification",
          type: "POST",
          args: {
            notification_type: values.notification_type,
            template: match[1],
            reference_doctype: frm.doctype,
            reference_name: frm.doc.name,
            primary_recipient: values.primary_recipient,
            cc_json: JSON.stringify((values.cc || "").split(",").map((x) => x.trim()).filter(Boolean))
          },
          freeze: true,
          callback() { dialog.hide(); frm.reload_doc(); }
        });
      }
    });
    dialog.fields_dict.notification_type.df.onchange = () => {
      const values = dialog.get_values(true) || {};
      const match = choices.find((row) => row[0] === values.notification_type);
      if (!match || !values.primary_recipient) return;
      frappe.call({
        method: "qorg.qorg.volunteer_management.api.preview_notification",
        args: {
          notification_type: values.notification_type,
          template: match[1],
          reference_doctype: frm.doctype,
          reference_name: frm.doc.name,
          primary_recipient: values.primary_recipient,
          cc_json: "[]"
        },
        callback(r) {
          const message = r.message || {};
          dialog.fields_dict.preview.$wrapper.html(`<div class="qorg-message-preview"><h5>${frappe.utils.escape_html(message.subject || "")}</h5>${message.message || ""}</div>`);
        }
      });
    };
    dialog.show();
  }

  Object.keys(CONFIG).forEach((doctype) => {
    frappe.ui.form.on(doctype, {
      refresh(frm) {
        if (frm.is_new() || !frappe.user.has_role(["Volunteer Coordinator", "Volunteer Manager", "System Manager"])) return;
        frm.add_custom_button(__("Preview or Send Communication"), () => openCommunication(frm), __("Communications"));
      }
    });
  });
})();
