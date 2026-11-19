frappe.ui.form.on("Funding Agreement",{
 setup(frm){set_funding_queries(frm);},refresh(frm){set_funding_queries(frm);toggle_exchange_fields(frm);},
 company(frm){frm.set_value("project",null);clear_exchange_data(frm);set_funding_queries(frm);},
 project(frm){if(!frm.doc.project){frm.set_value("project_funding_source_row",null);}else{frappe.db.get_value("Project",frm.doc.project,["company","expected_start_date","expected_end_date"]).then(r=>{if(r.message.company!==frm.doc.company){frm.set_value("project",null);frappe.throw(__("Project must belong to the selected Company."));}if(!frm.doc.start_date)frm.set_value("start_date",r.message.expected_start_date);if(!frm.doc.end_date)frm.set_value("end_date",r.message.expected_end_date);if(!frm.doc.eligibility_start_date)frm.set_value("eligibility_start_date",r.message.expected_start_date);if(!frm.doc.eligibility_end_date)frm.set_value("eligibility_end_date",r.message.expected_end_date);});}},
 donor(frm){if(!frm.doc.donor)frm.set_value("agreement_reference",null);},
 agreement_currency(frm){clear_exchange_data(frm);},
 exchange_rate_type(frm){clear_exchange_data(frm);toggle_exchange_fields(frm);},
 exchange_rate_date(frm){if(frm.doc.exchange_rate_type==="Transaction Date")frm.set_value("exchange_rate",0);},
 start_date(frm){if(!frm.doc.eligibility_start_date)frm.set_value("eligibility_start_date",frm.doc.start_date);},
 end_date(frm){if(!frm.doc.eligibility_end_date)frm.set_value("eligibility_end_date",frm.doc.end_date);}
});
function set_funding_queries(frm){frm.set_query("project",()=>({filters:{company:frm.doc.company||"",status:["not in",["Completed","Cancelled"]]}}));}
function clear_exchange_data(frm){if(!frm.doc.exchange_rate_locked){["exchange_rate","exchange_rate_date","exchange_rate_source","base_amount","manual_rate_approval_reference"].forEach(f=>frm.set_value(f,null));}}
function toggle_exchange_fields(frm){const manual=frm.doc.exchange_rate_type==="Manual Approved",fixed=frm.doc.exchange_rate_type==="Agreement Fixed";frm.toggle_reqd("exchange_rate",manual||fixed);frm.toggle_reqd("manual_rate_approval_reference",manual);frm.set_df_property("exchange_rate","read_only",frm.doc.exchange_rate_locked||!(manual||fixed));}
