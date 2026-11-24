frappe.ui.form.on('Employee Document Record', {
  setup(frm) {
    frm.set_query('document_type',()=>({filters:{is_active:1}}));
    frm.set_query('requirement',()=>({filters:{document_type:frm.doc.document_type||'',is_active:1}}));
    frm.set_query('supersedes_document',()=>({filters:{subject_doctype:frm.doc.subject_doctype||'',subject_name:frm.doc.subject_name||'',document_type:frm.doc.document_type||'',docstatus:1,status:['not in',['Superseded','Revoked','Rejected','Expired']]}}));
  },
  refresh(frm){set_storage_visibility(frm);set_verification_access(frm);},
  storage_type(frm){clear_storage_values(frm);set_storage_visibility(frm);},
  external_url(frm){if(frm.doc.external_url) hydrate_external_url(frm);},
  subject_doctype(frm){frm.set_value('subject_name','');frm.set_value('requirement','');},
  subject_name(frm){if(frm.doc.subject_name) hydrate_context(frm);},
  document_type(frm){frm.set_value('requirement','');if(frm.doc.document_type) hydrate_document_type(frm);},
  requirement(frm){if(frm.doc.requirement) hydrate_requirement(frm);}
});
function set_storage_visibility(frm){
  const t=frm.doc.storage_type;
  const external=['External URL','Microsoft SharePoint / OneDrive','Google Drive','External Document Management System','Reference Only'].includes(t);
  frm.toggle_display('external_url',external);
  frm.toggle_reqd('external_url',external);
  frm.toggle_display('attachment',t==='Frappe Attachment');frm.toggle_reqd('attachment',t==='Frappe Attachment');
  frm.toggle_display('repository_name',t==='External Document Management System');
  frm.toggle_display('physical_location',t==='Physical Document');frm.toggle_reqd('physical_location',t==='Physical Document');
  frm.toggle_display('archive_reference',t==='Physical Document');
  ['storage_provider','external_document_id','external_version_id','requires_authentication','microsoft_site_url','microsoft_drive_id','microsoft_item_id','microsoft_tenant','google_file_id','google_shared_drive_id'].forEach(f=>frm.toggle_display(f,false));
}
function set_verification_access(frm){
  const can_verify=frappe.user_roles.includes('HR Manager')||frappe.user_roles.includes('System Manager');
  ['verification_status','verification_method','verification_notes','rejection_reason','access_verification_status','access_verification_notes','confidentiality_level'].forEach(f=>frm.set_df_property(f,'read_only',can_verify?0:1));
}
function clear_storage_values(frm){
  const t=frm.doc.storage_type;
  if(t!=='Frappe Attachment'){frm.set_value('attachment','');frm.set_value('file_reference','');}
  if(!['External URL','Microsoft SharePoint / OneDrive','Google Drive','External Document Management System','Reference Only'].includes(t))frm.set_value('external_url','');
  if(t!=='External Document Management System')frm.set_value('repository_name','');
  if(t!=='Physical Document'){frm.set_value('physical_location','');frm.set_value('archive_reference','');}
}
function hydrate_external_url(frm){
  frappe.call({method:'qorg.qorg.employee_lifecycle.documents.parse_external_document_url',args:{storage_type:frm.doc.storage_type,url:frm.doc.external_url}}).then(r=>Object.entries(r.message||{}).forEach(([k,v])=>frm.set_value(k,v||'')));
}
function hydrate_context(frm){
  frappe.call({method:'qorg.qorg.employee_lifecycle.documents.document_subject_context',args:{subject_doctype:frm.doc.subject_doctype,subject_name:frm.doc.subject_name}}).then(r=>{const x=r.message||{};if(!frm.doc.document_title&&x.title)frm.set_value('document_title',x.title);});
}
function hydrate_document_type(frm){
  frappe.db.get_doc('Employee Document Type',frm.doc.document_type).then(d=>{if(!frm.doc.document_title)frm.set_value('document_title',d.document_type_name||d.name);if(d.default_confidentiality_level)frm.set_value('confidentiality_level',d.default_confidentiality_level);});
}
function hydrate_requirement(frm){
  frappe.db.get_doc('Employee Document Requirement',frm.doc.requirement).then(d=>{if(d.document_type&&d.document_type!==frm.doc.document_type)frm.set_value('document_type',d.document_type);});
}
