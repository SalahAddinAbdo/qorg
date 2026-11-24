frappe.ui.form.on('Appraisal Cycle', {
  setup(frm){frm.set_query('qorg_evaluation_type',()=>({filters:{active:1}}));},
  qorg_evaluation_type(frm){if(!frm.is_new() && frm.doc.qorg_policy_snapshot)frappe.show_alert({message:__('Changing Evaluation Type is blocked after Appraisals exist.'),indicator:'orange'});}
});
