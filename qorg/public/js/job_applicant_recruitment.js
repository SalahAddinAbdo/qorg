frappe.ui.form.on("Job Applicant", {
  refresh(frm) {
    if (frm.is_new()) return;
    const canReview = frappe.user.has_role(["Recruitment User", "Recruitment Manager", "HR Manager"]);
    const canManage = frappe.user.has_role(["Recruitment Manager", "HR Manager"]);
    if (canReview) frm.add_custom_button(__("Complete Screening"), () => frappe.prompt([
      {fieldname:"status",label:__("Result"),fieldtype:"Select",options:["Eligible","Shortlisted","Not Eligible"].join(String.fromCharCode(10)),reqd:1},
      {fieldname:"remarks",label:__("Remarks"),fieldtype:"Small Text"}
    ], v => frappe.call({method:"qorg.qorg.recruitment_extensions.api.complete_screening",args:{name:frm.doc.name,...v},freeze:true,callback:()=>frm.reload_doc()})), __("Recruitment"));
    if (canManage) {
      frm.add_custom_button(__("Recalculate Recruitment Scores"), () => frappe.call({method:"qorg.qorg.recruitment_extensions.api.recalculate_recruitment_scores",args:{name:frm.doc.name},freeze:true,callback:()=>frm.reload_doc()}), __("Recruitment"));
      frm.add_custom_button(__("Record Final Decision"), () => frappe.prompt([
        {fieldname:"decision",label:__("Decision"),fieldtype:"Select",options:["Selected","Reserve / Waitlisted","Rejected","Withdrawn","No Show","Disqualified","Cancelled"].join(String.fromCharCode(10)),reqd:1},
        {fieldname:"priority",label:__("Selection Priority"),fieldtype:"Int"},
        {fieldname:"remarks",label:__("Evidence-based Rationale"),fieldtype:"Small Text",reqd:1}
      ], v => frappe.call({method:"qorg.qorg.recruitment_extensions.api.record_final_decision",args:{name:frm.doc.name,...v},freeze:true,callback:()=>frm.reload_doc()})), __("Recruitment"));
      if (["Selected","Reserve / Waitlisted"].includes(frm.doc.qorg_final_decision)) frm.add_custom_button(__("Create Job Offer"), () => frappe.call({method:"qorg.qorg.recruitment_extensions.api.create_job_offer",args:{applicant:frm.doc.name},freeze:true,callback:r=>frappe.set_route("Form","Job Offer",r.message)}), __("Create"));
    }
  }
});
