frappe.ui.form.on('Evaluation Type', {
  setup(frm){frm.set_query('rating_scale',()=>({filters:{active:1}}));},
  validate(frm){
    const included=(frm.doc.sources||[]).filter(x=>x.include_score).reduce((sum,x)=>sum+flt(x.weight),0);
    if(Math.abs(included-100)>0.001) frappe.throw(__('Included source weights must total 100%. Current total: {0}',[included]));
  }
});
frappe.ui.form.on('Evaluation Source', {
  source(frm,cdt,cdn){const row=locals[cdt][cdn];if(['Goals','Self'].includes(row.source)){frappe.model.set_value(cdt,cdn,'assignment_required',0);frappe.model.set_value(cdt,cdn,'required_reviewers',1);frappe.model.set_value(cdt,cdn,'min_reviews',1);}},
  required_reviewers(frm,cdt,cdn){const row=locals[cdt][cdn];if(flt(row.min_reviews)>flt(row.required_reviewers))frappe.model.set_value(cdt,cdn,'min_reviews',row.required_reviewers);},
  anonymous(frm,cdt,cdn){const row=locals[cdt][cdn];if(row.anonymous){frappe.model.set_value(cdt,cdn,'min_anonymous_group',row.min_anonymous_group||3);}},
  include_score(frm,cdt,cdn){const row=locals[cdt][cdn];if(!row.include_score)frappe.model.set_value(cdt,cdn,'weight',0);}
});
