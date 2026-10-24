frappe.ui.form.on("Interview", {
  refresh(frm) {
    if (frm.is_new() || frm.doc.docstatus === 2 || !frappe.user.has_role(["HR Manager", "Recruitment Manager"])) return;
    frappe.call({method:"qorg.qorg.recruitment_extensions.api.get_retry_eligibility",args:{interview:frm.doc.name},callback(r){
      const result=r.message||{};
      if(!result.allowed)return;
      frm.add_custom_button(__(result.existing?"Open Retry Interview":"Create Retry Interview"),()=>{
        if(result.existing){frappe.set_route("Form","Interview",result.existing);return;}
        frappe.prompt([{fieldname:"retry_reason",label:__("Retry Reason"),fieldtype:"Small Text",reqd:1},{fieldname:"reuse_interviewers",label:__("Reuse Interviewers"),fieldtype:"Check",default:0}],values=>frappe.call({method:"qorg.qorg.recruitment_extensions.api.create_retry_interview",args:{interview:frm.doc.name,...values},freeze:true,callback:x=>frappe.set_route("Form","Interview",x.message)}));
      },__("Assessment"));
    }});
  }
});
