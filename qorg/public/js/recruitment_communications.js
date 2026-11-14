(() => {
  const CONFIG = {
    "Job Applicant": [["Application Not Selected", "Recruitment - Application Not Selected - Bilingual"], ["Reserve Candidate", "Recruitment - Reserve Candidate - Bilingual"]],
    "Interview": [["Interview Invitation", "Recruitment - Interview Invitation - Bilingual"], ["Interview Rescheduled", "Recruitment - Interview Rescheduled - Bilingual"], ["Missing Feedback Request", "Recruitment - Missing Feedback Request - Bilingual"]],
    "Interview Feedback": [["Missing Feedback Request", "Recruitment - Missing Feedback Request - Bilingual"]],
    "Job Offer": [["Job Offer Issued", "Recruitment - Job Offer Issued - Bilingual"]],
    "Appointment Letter": [["Appointment Letter Issued", "Recruitment - Appointment Letter Issued - Bilingual"]],
    "Employee Onboarding": [["Onboarding Activity Assigned", "Recruitment - Onboarding Activity Assigned - Bilingual"]],
    "Employee Boarding Activity": [["Onboarding Activity Assigned", "Recruitment - Onboarding Activity Assigned - Bilingual"]],
    "Work Commencement Notice": [["Work Commencement Internal Notice", "Recruitment - Work Commencement Internal Notice - Bilingual"]]
  };
  const recipient = (frm) => frm.doc.email_id || frm.doc.email || frm.doc.personal_email || frm.doc.company_email || "";
  function preview(frm, dialog, values) {
    const pair=(CONFIG[frm.doctype]||[]).find((row)=>row[0]===values.notification_type);
    if(!pair||!values.primary_recipient)return;
    frappe.call({method:"qorg.qorg.recruitment_extensions.notifications.preview_recruitment_message",args:{template:pair[1],reference_doctype:frm.doctype,reference_name:frm.doc.name,primary_recipient:values.primary_recipient,cc_json:JSON.stringify((values.cc||"").split(",").map((x)=>x.trim()).filter(Boolean)),notification_type:values.notification_type},callback(r){const m=r.message||{};dialog.fields_dict.preview.$wrapper.html(`<div class="qorg-message-preview"><h5>${frappe.utils.escape_html(m.subject||"")}</h5>${m.message||""}</div>`);}});
  }
  function open(frm) {
    const choices=CONFIG[frm.doctype]||[];
    const dialog=new frappe.ui.Dialog({title:__("Recruitment Communication"),fields:[{fieldname:"notification_type",label:__("Communication Type"),fieldtype:"Select",options:choices.map((x)=>x[0]).join("\n"),reqd:1},{fieldname:"primary_recipient",label:__("Primary Recipient"),fieldtype:"Data",options:"Email",default:recipient(frm),reqd:1},{fieldname:"cc",label:__("CC"),fieldtype:"Data",description:__("Comma-separated email addresses")},{fieldname:"preview",label:__("Preview"),fieldtype:"HTML"}],primary_action_label:__("Send"),primary_action(values){const pair=choices.find((x)=>x[0]===values.notification_type);if(!pair)return;frappe.call({method:"qorg.qorg.recruitment_extensions.notifications.send_managed_recruitment_message",type:"POST",freeze:true,args:{notification_type:values.notification_type,template:pair[1],reference_doctype:frm.doctype,reference_name:frm.doc.name,primary_recipient:values.primary_recipient,cc_json:JSON.stringify((values.cc||"").split(",").map((x)=>x.trim()).filter(Boolean))},callback(){dialog.hide();frm.reload_doc();}});}});
    dialog.fields_dict.notification_type.df.onchange=()=>preview(frm,dialog,dialog.get_values(true)||{});dialog.show();
  }
  Object.keys(CONFIG).forEach((doctype)=>frappe.ui.form.on(doctype,{refresh(frm){if(frm.is_new()||!frappe.user.has_role(["HR Manager","HR User","System Manager"]))return;frm.add_custom_button(__("Preview or Send Communication"),()=>open(frm),__("Communications"));}}));
})();
