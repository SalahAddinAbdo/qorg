frappe.ui.form.on('Employee Performance Feedback', {
  setup(frm) {
    frm.set_query('qorg_assignment', () => ({filters:{employee:frm.doc.employee||'',reviewer:frm.doc.reviewer||'',status:['in',['Assigned','In Progress']]}}));
    frm.set_query('qorg_evidence', () => ({filters:{subject_doctype:'Employee',subject_name:frm.doc.employee||'',status:'Verified'}}));
  },
  refresh(frm) {
    if (frm.doc.qorg_assignment && frm.doc.docstatus===0) {
      frm.set_intro(__('Comments or verified evidence may be mandatory when the normalized score is below the source policy threshold.'),'blue');
    }
  }
});
