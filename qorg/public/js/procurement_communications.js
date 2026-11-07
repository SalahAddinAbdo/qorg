frappe.provide('qorg.procurement');
qorg.procurement.preview_and_send = function(frm, template_name, default_recipient) {
  frappe.call({method:'qorg.qorg.procurement_contracting.communications.preview_template',args:{reference_doctype:frm.doctype,reference_name:frm.doc.name,template_name}}).then(r => {
    const d=new frappe.ui.Dialog({title:__('Preview Email'),fields:[
      {fieldname:'recipients',fieldtype:'Data',label:__('Recipients'),reqd:1,default:default_recipient||''},
      {fieldname:'cc',fieldtype:'Data',label:__('CC')},
      {fieldname:'subject',fieldtype:'Data',label:__('Subject'),read_only:1,default:r.message.subject},
      {fieldname:'message',fieldtype:'HTML',label:__('Message'),options:r.message.message}
    ],primary_action_label:__('Send'),primary_action(values){
      frappe.call({method:'qorg.qorg.procurement_contracting.communications.send_template',args:{reference_doctype:frm.doctype,reference_name:frm.doc.name,template_name,recipients:values.recipients,cc:values.cc},freeze:true,freeze_message:__('Sending...')}).then(()=>{d.hide();frappe.show_alert({message:__('Email queued successfully'),indicator:'green'});});
    }}); d.show();
  });
};
