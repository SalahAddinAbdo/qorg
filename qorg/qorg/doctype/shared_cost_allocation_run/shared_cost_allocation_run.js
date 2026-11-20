frappe.ui.form.on("Shared Cost Allocation Run",{
 setup(frm){set_run_queries(frm);},refresh(frm){set_run_queries(frm);if(frm.doc.docstatus===0)frm.add_custom_button(__("Refresh Preview"),()=>frm.save());  if(frm.doc.journal_entry)frm.add_custom_button(__("Open Journal Entry"),()=>frappe.set_route("Form","Journal Entry",frm.doc.journal_entry),__("Accounting"));
  if(frm.doc.reversal_journal_entry)frm.add_custom_button(__("Open Reversal Journal Entry"),()=>frappe.set_route("Form","Journal Entry",frm.doc.reversal_journal_entry),__("Accounting"));
  if(frm.doc.journal_entry&&frm.doc.run_status==="Journal Draft Created")frm.add_custom_button(__("Delete Draft Journal Entry"),()=>delete_draft_journal(frm,"Original"),__("Accounting"));
  if(frm.doc.reversal_journal_entry&&frm.doc.run_status==="Reversal Draft Created")frm.add_custom_button(__("Delete Draft Reversal Entry"),()=>delete_draft_journal(frm,"Reversal"),__("Accounting"));
  if(frm.doc.docstatus===1&&frm.doc.run_status==="Posted")frm.add_custom_button(__("Rollback Allocation"),()=>open_rollback_dialog(frm),__("Accounting"));},
 allocation_rule(frm){clear_run_rule_dependents(frm);if(frm.doc.allocation_rule)load_rule_defaults(frm);set_run_queries(frm);},
 run_type(frm){if(frm.doc.run_type!=="Adjustment"){frm.set_value("adjustment_of",null);frm.set_value("adjustment_reason",null);frm.set_value("donor_approval_reference",null);}set_run_queries(frm);},
 period_start(frm){if(frm.doc.period_end&&frm.doc.period_start>frm.doc.period_end)frm.set_value("period_end",null);},
 period_end(frm){if(frm.doc.period_start&&frm.doc.period_end<frm.doc.period_start)frm.set_value("period_start",null);},
 validate(frm){if(frm.doc.run_type==="Adjustment"&&!frm.doc.adjustment_of)frappe.throw(__("Adjustment Of is required."));}
});
function set_run_queries(frm){frm.set_query("allocation_rule",()=>({filters:{docstatus:1,status:"Active"}}));frm.set_query("adjustment_of",()=>({filters:{docstatus:1,allocation_rule:frm.doc.allocation_rule||"",run_status:"Posted"}}));}
function clear_run_rule_dependents(frm){["company","allocation_category","allocation_method","source_cost_center","company_currency","period_start","period_end","posting_date","adjustment_of","journal_entry","reversal_journal_entry"].forEach(f=>frm.set_value(f,null));frm.clear_table("entries");frm.refresh_field("entries");}
function load_rule_defaults(frm){return frappe.call({method:"qorg.qorg.shared_cost_allocation.api.get_rule_defaults",args:{rule:frm.doc.allocation_rule}}).then(r=>{const d=r.message||{};frm.set_value("company",d.company);frm.set_value("allocation_category",d.allocation_category);frm.set_value("allocation_method",d.allocation_method);frm.set_value("source_cost_center",d.source_cost_center);frm.set_value("company_currency",d.currency);if(!frm.doc.period_start)frm.set_value("period_start",d.period_start);if(!frm.doc.period_end&&d.period_end)frm.set_value("period_end",d.period_end);if(!frm.doc.posting_date)frm.set_value("posting_date",d.posting_date);});}

function open_reversal_dialog(frm){
 frappe.prompt([
  {fieldname:"posting_date",label:__("Reversal Posting Date"),fieldtype:"Date",default:frappe.datetime.get_today(),reqd:1},
  {fieldname:"reason",label:__("Reversal Reason"),fieldtype:"Small Text",reqd:1}
 ],values=>frappe.call({method:"qorg.qorg.shared_cost_allocation.engine.create_draft_reversal_entry",args:{run_name:frm.doc.name,posting_date:values.posting_date,reason:values.reason},freeze:true,callback:r=>{frm.reload_doc();frappe.set_route("Form","Journal Entry",r.message);}}),__("Create Draft Reversal Entry"),__("Create Draft"));
}

function open_rollback_dialog(frm){
 frappe.call({method:"qorg.qorg.shared_cost_allocation.engine.get_allocation_rollback_options",args:{run_name:frm.doc.name},freeze:true,callback:r=>{
  const x=r.message||{},options=[];
  if(x.controlled_cancellation_allowed)options.push("Controlled Cancellation");
  if(x.reversal_allowed)options.push("Reversal Entry");
  if(!options.length){frappe.msgprint(x.controlled_cancellation_reason||__("No rollback method is currently available."));return;}
  const d=new frappe.ui.Dialog({title:__("Rollback Allocation"),fields:[
   {fieldname:"method",label:__("Rollback Method"),fieldtype:"Select",options:options.join("\n"),default:options[0],reqd:1},
   {fieldname:"posting_date",label:__("Reversal Posting Date"),fieldtype:"Date",default:frappe.datetime.get_today(),depends_on:'eval:doc.method==="Reversal Entry"'},
   {fieldname:"reason",label:__("Rollback Reason"),fieldtype:"Small Text",reqd:1},
   {fieldname:"policy",label:__("Company Policy"),fieldtype:"Data",default:x.policy,read_only:1},
   {fieldname:"notice",fieldtype:"HTML",options:x.controlled_cancellation_allowed?"":`<div class="alert alert-warning">${x.controlled_cancellation_reason||""}</div>`}
  ],primary_action_label:__("Continue"),primary_action:v=>{
   const method=v.method==="Controlled Cancellation"?"qorg.qorg.shared_cost_allocation.engine.controlled_cancel_allocation_run":"qorg.qorg.shared_cost_allocation.engine.create_draft_reversal_entry";
   const args=v.method==="Controlled Cancellation"?{run_name:frm.doc.name,reason:v.reason}:{run_name:frm.doc.name,posting_date:v.posting_date,reason:v.reason};
   frappe.call({method,args,freeze:true,callback:res=>{d.hide();if(v.method==="Reversal Entry")frappe.set_route("Form","Journal Entry",res.message);else frappe.set_route("Form","Shared Cost Allocation Run",frm.doc.name);}});
  }});d.show();
 }});
}

function delete_draft_journal(frm,journal_kind){
 const label=journal_kind==="Reversal"?__("draft reversal Journal Entry"):__("draft Journal Entry");
 frappe.confirm(__("Delete the linked {0}? This is allowed only while the Journal Entry is still Draft.",[label]),()=>frappe.prompt([
  {fieldname:"confirmation",label:__("Type DELETE to confirm"),fieldtype:"Data",reqd:1}
 ],v=>{
  if((v.confirmation||"").trim().toUpperCase()!=="DELETE"){frappe.msgprint(__("Confirmation text must be DELETE."));return;}
  frappe.call({method:"qorg.qorg.shared_cost_allocation.engine.delete_draft_allocation_journal",args:{run_name:frm.doc.name,journal_kind},freeze:true,callback:r=>{frappe.show_alert({message:__("Draft Journal Entry deleted."),indicator:"green"});frm.reload_doc();}});
 },__("Delete Draft Journal Entry"),__("Delete")));
}
