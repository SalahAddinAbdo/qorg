frappe.ui.form.on('Development Action', {
  setup(frm) {
    frm.set_query('employee', () => ({filters:{status:'Active'}}));
    frm.set_query('responsible_person', () => ({filters:{enabled:1,user_type:'System User'}}));
    frm.set_query('source_doctype', () => ({filters:{name:['in', source_doctypes(frm.doc.source_type)]}}));
    frm.set_query('source_document', () => action_source_query(frm));
    frm.set_query('skill', () => ({filters:{name:['!=','']}}));
    frm.set_query('training_need_request', () => ({filters:{status:['not in',['Rejected','Cancelled']],requested_for_employee:frm.doc.employee||''}}));
    frm.set_query('completion_document', () => ({filters:{subject_doctype:'Employee',subject_name:frm.doc.employee||'',status:'Verified'}}));
  },
  source_type(frm) {
    const allowed=source_doctypes(frm.doc.source_type);
    if (allowed.length===1) frm.set_value('source_doctype',allowed[0]);
    if (frm.doc.source_doctype && !allowed.includes(frm.doc.source_doctype)) {frm.set_value('source_doctype','');frm.set_value('source_document','');}
  },
  action_type(frm) { if (frm.doc.action_type!=='Training') frm.set_value('training_need_request',''); },
  status(frm) {
    if (frm.doc.status!=='Completed') ['completion_date','completion_evidence_type','completion_document','completion_url','completion_notes'].forEach(f=>frm.set_value(f,''));
  }
});
function source_doctypes(type) {
  return {'Appraisal':['Appraisal'],'Skill Assessment':['Employee Skill Map'],'Performance Feedback':['Employee Performance Feedback'],'Training Follow-up':['Training Follow-up'],'Manager Decision':['Employee'],'Compliance Requirement':['Employee Document Requirement']}[type] || ['Appraisal','Employee Skill Map','Employee Performance Feedback','Employee Document Requirement','Employee','Goal','Project'];
}

function action_source_query(frm){
  const dt=frm.doc.source_doctype;if(!dt)return {filters:{name:''}};const filters={};
  if(['Appraisal','Employee Skill Map','Employee Performance Feedback'].includes(dt) && frm.doc.employee) filters.employee=frm.doc.employee;
  if(dt==='Appraisal') filters.docstatus=1;
  if(dt==='Employee Document Requirement') filters.is_active=1;
  if(dt==='Employee') filters.name=frm.doc.employee||'';
  return {filters};
}
