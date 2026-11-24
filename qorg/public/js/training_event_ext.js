frappe.ui.form.on('Training Event', {
  refresh(frm) {
    if (frm.is_new()) return;
    frm.add_custom_button(__('Recalculate Results'),()=>frappe.call({method:'qorg.qorg.employee_lifecycle.training_api.recalculate',args:{training_event:frm.doc.name},freeze:true}).then(r=>frappe.msgprint(r.message?__('Training Result recalculated.'):__('No Training Result exists yet.'))),__('Learning'));
    if (frm.doc.qorg_follow_up_required) frm.add_custom_button(__('Create Follow-ups'),()=>frappe.call({method:'qorg.qorg.employee_lifecycle.training_api.create_follow_ups',args:{training_event:frm.doc.name},freeze:true}).then(r=>frappe.msgprint(__('Created {0}; existing {1}.',[(r.message.created||[]).length,(r.message.existing||[]).length]))),__('Learning'));
  },
  training_program(frm){
    if(!frm.doc.training_program)return;
    frappe.db.get_doc('Training Program',frm.doc.training_program).then(p=>{
      const map={qorg_min_attendance:'qorg_min_attendance',qorg_pre_assessment_required:'qorg_pre_assessment_required',qorg_post_assessment_required:'qorg_post_assessment_required',qorg_feedback_required:'qorg_feedback_required',qorg_follow_up_required:'qorg_follow_up_required',qorg_follow_up_days:'qorg_follow_up_days'};
      Object.entries(map).forEach(([t,s])=>{if(frm.doc[t]===undefined||frm.doc[t]===null||frm.doc[t]==='')frm.set_value(t,p[s]);});
    });
  }
});
frappe.ui.form.on('Training Event Employee', {
  qorg_attendance_status(frm,cdt,cdn){const row=locals[cdt][cdn];const defaults={'Attended':100,'Partially Attended':50,'Absent':0,'Excused':0,'Not Recorded':0};frappe.model.set_value(cdt,cdn,'qorg_attendance_percentage',defaults[row.qorg_attendance_status]??0);set_eligibility(frm,row,cdt,cdn);},
  qorg_attendance_percentage(frm,cdt,cdn){set_eligibility(frm,locals[cdt][cdn],cdt,cdn);}
});
function set_eligibility(frm,row,cdt,cdn){const eligible=flt(row.qorg_attendance_percentage)>=flt(frm.doc.qorg_min_attendance||75);frappe.model.set_value(cdt,cdn,'qorg_post_eligible',eligible?1:0);frappe.model.set_value(cdt,cdn,'qorg_certificate_eligible',eligible&&frm.doc.has_certificate&&!frm.doc.qorg_post_assessment_required?1:0);}
