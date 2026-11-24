frappe.ui.form.on('Training Follow-up', {
  setup(frm) {
    frm.set_query('employee',()=>({query:'qorg.qorg.employee_lifecycle.training_query.event_employees',filters:{training_event:frm.doc.training_event||''}}));
    frm.set_query('training_event',()=>({filters:{docstatus:1,event_status:['not in',['Cancelled']]}}));
    frm.set_query('training_result',()=>({filters:{training_event:frm.doc.training_event||'',docstatus:1}}));
    frm.set_query('responsible_user',()=>({filters:{enabled:1,user_type:'System User'}}));
    frm.set_query('evidence_document',()=>({filters:{subject_doctype:'Employee',subject_name:frm.doc.employee||'',status:'Verified'}}));
    frm.set_query('recommended_action',()=>({filters:{employee:frm.doc.employee||'',source_type:'Training Follow-up',source_document:frm.doc.name||'',status:['not in',['Completed','Cancelled']]}}));
  },
  training_event(frm){frm.set_value('employee','');frm.set_value('training_result','');},
  evidence_type(frm){if(frm.doc.evidence_type!=='Employee Document Record')frm.set_value('evidence_document','');if(frm.doc.evidence_type!=='External URL')frm.set_value('evidence_url','');},
  additional_training_required(frm){if(!frm.doc.additional_training_required)frm.set_value('recommended_action','');}
});
