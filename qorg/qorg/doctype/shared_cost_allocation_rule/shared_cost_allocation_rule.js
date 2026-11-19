frappe.ui.form.on("Shared Cost Allocation Rule", {
 setup(frm){set_rule_queries(frm);},
 refresh(frm){set_rule_queries(frm);apply_rule_visibility(frm);if(frm.doc.docstatus===1&&frm.doc.status==="Active")frm.add_custom_button(__("Create Changed Rule"),()=>open_change_dialog(frm));},
 company(frm){clear_rule_company_dependents(frm);if(frm.doc.company)load_company_defaults(frm);set_rule_queries(frm);},
 allocation_category(frm){clear_indirect_fields_if_needed(frm);if(frm.doc.company)load_company_defaults(frm);apply_rule_visibility(frm);},
 allocation_method(frm){clear_inapplicable_driver_values(frm);apply_rule_visibility(frm);frm.refresh_field("targets");},
 source_selection_mode(frm){clear_inapplicable_sources(frm);apply_rule_visibility(frm);},
 effective_from(frm){if(frm.doc.effective_to&&frm.doc.effective_from>frm.doc.effective_to)frm.set_value("effective_to",null);},
 validate(frm){validate_client_totals(frm);}
});
frappe.ui.form.on("Shared Cost Allocation Target", {
 project(frm,cdt,cdn){const row=locals[cdt][cdn];clear_target_from_project(cdt,cdn);set_target_queries(frm,cdt,cdn);if(row.project)load_target_defaults(frm,cdt,cdn);},
 budget_line(frm,cdt,cdn){clear_target_from_budget_line(cdt,cdn);if(locals[cdt][cdn].budget_line)load_target_defaults(frm,cdt,cdn);},
 funding_agreement(frm,cdt,cdn){clear_target_from_agreement(cdt,cdn);if(locals[cdt][cdn].funding_agreement)load_target_defaults(frm,cdt,cdn);},
 targets_add(frm,cdt,cdn){frappe.model.set_value(cdt,cdn,"allow_allocation",1);set_target_queries(frm,cdt,cdn);}
});
frappe.ui.form.on("Shared Cost Source Filter",{account(frm,cdt,cdn){const row=locals[cdt][cdn];if(row.account)frappe.db.get_value("Account",row.account,["company","is_group"]).then(r=>{if(r.message.company!==frm.doc.company){frappe.model.set_value(cdt,cdn,"account",null);frappe.throw(__("Account must belong to the selected Company."));}if(!r.message.is_group)frappe.model.set_value(cdt,cdn,"include_children",0);});}});
frappe.ui.form.on("Shared Cost Source Voucher",{voucher_type(frm,cdt,cdn){frappe.model.set_value(cdt,cdn,"voucher_no",null);}});
function set_rule_queries(frm){
 frm.set_query("source_cost_center",()=>({filters:{company:frm.doc.company||"",is_group:0}}));
 frm.set_query("source_project",()=>({filters:{company:frm.doc.company||"",status:["not in",["Completed","Cancelled"]]}}));
 frm.set_query("indirect_cost_expense_account",()=>({filters:{company:frm.doc.company||"",is_group:0,root_type:"Expense"}}));
 frm.set_query("indirect_cost_recovery_account",()=>({filters:{company:frm.doc.company||"",is_group:0,root_type:["in",["Income","Equity"]]}}));
 frm.set_query("account","source_filters",()=>({filters:{company:frm.doc.company||""}}));
 frm.set_query("voucher_no","selected_vouchers",(doc,cdt,cdn)=>{const row=locals[cdt][cdn];return{filters:{docstatus:["<",2]},query:"frappe.desk.search.search_link",doctype:row.voucher_type||""};});
 frm.fields_dict.targets?.grid?.grid_rows?.forEach(r=>set_target_queries(frm,r.doc.doctype,r.doc.name));
}
function set_target_queries(frm,cdt,cdn){const row=locals[cdt][cdn];
 frm.set_query("project","targets",()=>({filters:{company:frm.doc.company||"",status:["not in",["Completed","Cancelled"]]}}));
 frm.set_query("cost_center","targets",()=>({filters:{company:frm.doc.company||"",is_group:0}}));
 frm.set_query("budget_line","targets",()=>({filters:{project:row.project||"",is_group:0,status:["!=","Inactive"]}}));
 frm.set_query("funding_agreement","targets",()=>({filters:{company:frm.doc.company||"",project:row.project||"",status:["in",["Active"]],docstatus:1}}));
}
function load_company_defaults(frm){return frappe.call({method:"qorg.qorg.shared_cost_allocation.api.get_company_defaults",args:{company:frm.doc.company}}).then(r=>{const d=r.message||{};if(!d.custom_enable_shared_cost_allocation)frappe.msgprint(__("Shared Cost Allocation is not enabled for this Company."));if(!frm.doc.source_cost_center)frm.set_value("source_cost_center",d.custom_shared_cost_default_cost_center);if(frm.doc.allocation_category==="Indirect Cost Recovery"){if(!frm.doc.indirect_cost_expense_account)frm.set_value("indirect_cost_expense_account",d.custom_indirect_cost_expense_account);if(!frm.doc.indirect_cost_recovery_account)frm.set_value("indirect_cost_recovery_account",d.custom_indirect_cost_recovery_account);}});}
function load_target_defaults(frm,cdt,cdn){const row=locals[cdt][cdn];return frappe.call({method:"qorg.qorg.shared_cost_allocation.api.get_target_defaults",args:{company:frm.doc.company,project:row.project,budget_line:row.budget_line,funding_agreement:row.funding_agreement}}).then(r=>{const d=r.message||{};["cost_center","funding_agreement","donor","eligibility_start_date","eligibility_end_date","indirect_rate_override"].forEach(f=>{if(d[f]!==undefined&&d[f]!==null&&(!row[f]||["donor","eligibility_start_date","eligibility_end_date"].includes(f)))frappe.model.set_value(cdt,cdn,f,d[f]);});});}
function clear_rule_company_dependents(frm){["source_cost_center","source_project","finance_book","indirect_cost_expense_account","indirect_cost_recovery_account"].forEach(f=>frm.set_value(f,null));frm.clear_table("source_filters");frm.clear_table("selected_vouchers");frm.clear_table("targets");frm.refresh_fields();}
function clear_indirect_fields_if_needed(frm){if(frm.doc.allocation_category!=="Indirect Cost Recovery"){["indirect_base_method","indirect_cost_expense_account","indirect_cost_recovery_account","total_recovery_cap"].forEach(f=>frm.set_value(f,null));frm.clear_table("rate_periods");frm.refresh_field("rate_periods");}}
function clear_inapplicable_sources(frm){if(frm.doc.source_selection_mode==="Filtered GL Entries")frm.clear_table("selected_vouchers");if(frm.doc.source_selection_mode==="Selected Vouchers Only"){frm.clear_table("source_filters");frm.set_value("voucher_types",null);}frm.refresh_fields();}
function clear_inapplicable_driver_values(frm){frm.doc.targets?.forEach(r=>{if(frm.doc.allocation_method!=="Fixed Percentage")frappe.model.set_value(r.doctype,r.name,"allocation_percentage",0);if(frm.doc.allocation_method!=="Fixed Amount")frappe.model.set_value(r.doctype,r.name,"fixed_amount",0);if(!["Manual Driver","Composite Driver"].includes(frm.doc.allocation_method))frappe.model.set_value(r.doctype,r.name,"driver_quantity",0);});if(frm.doc.allocation_method!=="Composite Driver")["direct_expenditure_weight","budget_weight","headcount_weight","beneficiary_weight","manual_weight"].forEach(f=>frm.set_value(f,0));}
function clear_target_from_project(cdt,cdn){["cost_center","budget_line","funding_agreement","donor","eligibility_start_date","eligibility_end_date","indirect_rate_override","donor_approval_reference"].forEach(f=>frappe.model.set_value(cdt,cdn,f,null));}
function clear_target_from_budget_line(cdt,cdn){["funding_agreement","donor","eligibility_start_date","eligibility_end_date","indirect_rate_override","donor_approval_reference"].forEach(f=>frappe.model.set_value(cdt,cdn,f,null));}
function clear_target_from_agreement(cdt,cdn){["donor","eligibility_start_date","eligibility_end_date","indirect_rate_override","donor_approval_reference"].forEach(f=>frappe.model.set_value(cdt,cdn,f,null));}
function apply_rule_visibility(frm){frm.toggle_display("rate_periods",frm.doc.allocation_category==="Indirect Cost Recovery");}
function validate_client_totals(frm){const active=(frm.doc.targets||[]).filter(r=>r.allow_allocation);if(frm.doc.allocation_method==="Fixed Percentage"){const total=active.reduce((s,r)=>s+flt(r.allocation_percentage),0);if(Math.abs(total-100)>.0001)frappe.throw(__("Allocation percentages must equal 100%. Current total: {0}%. Difference: {1}%.",[total,100-total]));}if(frm.doc.allocation_method==="Composite Driver"){const fields=["direct_expenditure_weight","budget_weight","headcount_weight","beneficiary_weight","manual_weight"];const total=fields.reduce((s,f)=>s+flt(frm.doc[f]),0);if(Math.abs(total-100)>.0001)frappe.throw(__("Composite driver weights must equal 100%. Current total: {0}%.",[total]));}}
function open_change_dialog(frm){frappe.prompt([{fieldname:"change_type",label:__("Change Type"),fieldtype:"Select",options:["Prospective Change","Donor Approved Increase","Donor Approved Reduction","Correction"].join("\n"),reqd:1},{fieldname:"change_effective_date",label:__("Change Effective Date"),fieldtype:"Date",reqd:1}],v=>frappe.call({method:"qorg.qorg.shared_cost_allocation.engine.create_changed_rule",args:{source_rule:frm.doc.name,change_type:v.change_type,change_effective_date:v.change_effective_date},callback:r=>frappe.set_route("Form","Shared Cost Allocation Rule",r.message)}),__("Create Changed Rule"));}
