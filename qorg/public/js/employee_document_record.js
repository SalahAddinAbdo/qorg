frappe.ui.form.on('Employee Document Record', {
  setup(frm) {
    frm.set_query('document_type',()=>({filters:{is_active:1}}));
    frm.set_query('requirement',()=>({filters:{document_type:frm.doc.document_type||'',is_active:1}}));
  },
  refresh: set_storage_visibility,
  storage_type: set_storage_visibility,
  subject_doctype(frm){frm.set_value('subject_name','');}
});
function set_storage_visibility(frm){
  const external=['External URL','Microsoft SharePoint / OneDrive','Google Drive','External Document Management System'].includes(frm.doc.storage_type);
  frm.toggle_display('external_url',external);
  frm.toggle_display('attachment',frm.doc.storage_type==='Frappe Attachment');
  frm.toggle_display('physical_location',frm.doc.storage_type==='Physical Document');
  frm.toggle_display('archive_reference',frm.doc.storage_type==='Physical Document');
}
