frappe.ui.form.on("Candidate Reference Check", {
  setup(frm) {
    frm.set_query("job_offer", () => ({filters: {qorg_job_applicant: frm.doc.job_applicant || "", qorg_response_status: "Accepted"}}));
    frm.set_query("job_applicant", () => ({filters: {qorg_final_decision: "Selected"}}));
  },
  refresh(frm) {
    const callAction = (method, confirmMessage) => frappe.confirm(__(confirmMessage), () => {
      frappe.call({method, args:{name:frm.doc.name}, freeze:true, freeze_message:__("Processing..."),
        callback:r => { if (!r.exc) frm.reload_doc(); }});
    });
    if (frm.is_new()) return;
    if (["Draft", "Ready to Send", "Follow-up Required"].includes(frm.doc.status)) {
      frm.add_custom_button(__("Send Reference Request"), () => callAction(
        "qorg.qorg.recruitment_extensions.reference_checks.send_reference_check_request",
        "Send the reference-check request and attached bilingual form now?"), __("Reference Check"));
    }
    if (["Sent", "Follow-up Required"].includes(frm.doc.status)) {
      frm.add_custom_button(__("Record Received"), () => callAction(
        "qorg.qorg.recruitment_extensions.reference_checks.record_reference_check_received",
        "Confirm that the reference response has been received?"), __("Reference Check"));
    }
    if (frm.doc.status === "Received") {
      frm.add_custom_button(__("Verify Result"), () => callAction(
        "qorg.qorg.recruitment_extensions.reference_checks.verify_reference_check",
        "Verify and lock this reference-check result?"), __("Reference Check"));
    }
    if (["Sent", "Follow-up Required"].includes(frm.doc.status)) {
      frm.add_custom_button(__("Record Follow-up"), () => callAction(
        "qorg.qorg.recruitment_extensions.reference_checks.record_reference_check_follow_up",
        "Record a follow-up reminder for this reference?"), __("Reference Check"));
    }
  },
  job_applicant(frm) { if (frm.doc.job_offer) frm.set_value("job_offer", null); }
});
