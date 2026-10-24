frappe.ui.form.on("Interview Type",{
 setup(frm){frm.__qorg_loading=false;},
 async designation(frm){await qorg_load_criteria(frm,true);},
 async qorg_assessment_type(frm){await qorg_load_criteria(frm,true);},
 refresh(frm){if(!frm.doc.designation)return;frm.add_custom_button(__("Append Missing Designation Criteria"),()=>qorg_load_criteria(frm,false,"append"),__("Criteria"));frm.add_custom_button(__("Replace with Designation Criteria"),()=>frappe.confirm(__("Replace current criteria?"),()=>qorg_load_criteria(frm,false,"replace")),__("Criteria"));},
 validate(frm){qorg_validate_total(frm.doc.qorg_evaluation_criteria||[],"weight",__("Evaluation Criteria weights"));}
});
frappe.ui.form.on("Interview Evaluation Criterion",{weight(frm){qorg_intro(frm);},qorg_evaluation_criteria_remove(frm){qorg_intro(frm);}});
async function qorg_load_criteria(frm,automatic,mode="replace_if_empty"){
 if(!frm.doc.designation||!frm.doc.qorg_assessment_type||frm.__qorg_loading)return;
 if(mode==="replace_if_empty"&&(frm.doc.qorg_evaluation_criteria||[]).length)return;
 frm.__qorg_loading=true;
 try{const r=await frappe.call({method:"qorg.qorg.recruitment_extensions.template_api.get_designation_criteria",args:{designation:frm.doc.designation,assessment_type:frm.doc.qorg_assessment_type},freeze:!automatic});const rows=r.message||[];if(!rows.length){if(!automatic)frappe.msgprint(__("No matching designation criteria found."));return;}if(mode!=="append")frm.clear_table("qorg_evaluation_criteria");const existing=new Set((frm.doc.qorg_evaluation_criteria||[]).map(x=>[x.competency_area||"",x.question_task||"",x.assessment_method||""].join("|")));rows.forEach(x=>{const key=[x.competency_area||"",x.question_task||"",x.assessment_method||""].join("|");if(existing.has(key))return;let row=frm.add_child("qorg_evaluation_criteria");Object.assign(row,{source_designation_criterion:x.name,sequence:x.sequence,competency_area:x.competency_area,question_task:x.question_task,assessment_method:x.assessment_method,weight:x.default_weight,passing_score:x.passing_score,is_mandatory:x.is_mandatory,low_score_anchor:x.low_score_anchor,mid_score_anchor:x.mid_score_anchor,high_score_anchor:x.high_score_anchor,instructions:x.instructions});existing.add(key);});frm.refresh_field("qorg_evaluation_criteria");frm.dirty();qorg_intro(frm);}finally{frm.__qorg_loading=false;}}
function qorg_total(rows,field){return flt((rows||[]).reduce((s,r)=>s+flt(r[field]),0),2);}
function qorg_intro(frm){const t=qorg_total(frm.doc.qorg_evaluation_criteria,"weight");frm.set_intro(__("Evaluation criteria weight total: {0}%",[t]),Math.abs(t-100)<=.01?"green":"orange");}
function qorg_validate_total(rows,field,label){if(!rows.length)return;const t=qorg_total(rows,field),d=flt(100-t,2);if(Math.abs(d)>.01)frappe.throw(__("{0} must total exactly 100%. Current total: {1}%. Please {2} {3}%.",[label,t,d>0?__("add"):__("remove"),Math.abs(d)]));}
