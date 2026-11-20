frappe.ui.form.on("Service and Allowance Accrual",{
 setup(frm){set_queries(frm);},
 refresh(frm){set_queries(frm);if(frm.doc.docstatus===1&&["Approved","Journal Draft Created"].includes(frm.doc.operational_status)){frm.add_custom_button(__("Create / Open Draft Journal Entry"),()=>frappe.call({method:"qorg.qorg.doctype.service_and_allowance_accrual.service_and_allowance_accrual.create_draft_journal_entry",args:{accrual:frm.doc.name},freeze:true,callback:r=>frappe.set_route("Form","Journal Entry",r.message)}),__("Accounting"));}},
 company(frm){frm.set_value("currency",null);frm.clear_table("lines");frm.refresh_field("lines");set_queries(frm);if(frm.doc.company)frappe.db.get_value("Company",frm.doc.company,"default_currency").then(r=>frm.set_value("currency",r.message.default_currency));},
 accrual_type(frm){if(!frm.doc.accrual_type)return;frappe.db.get_doc("Service and Allowance Type",frm.doc.accrual_type).then(t=>{frm.set_value("procurement_treatment",t.procurement_treatment);(frm.doc.lines||[]).forEach(r=>apply_type_defaults(r,t));frm.refresh_field("lines");});}
});
frappe.ui.form.on("Service and Allowance Accrual Line",{
 lines_add(frm,cdt,cdn){if(frm.doc.accrual_type)frappe.db.get_doc("Service and Allowance Type",frm.doc.accrual_type).then(t=>{apply_type_defaults(locals[cdt][cdn],t);frm.refresh_field("lines");});},
 beneficiary_type(frm,cdt,cdn){const r=locals[cdt][cdn];["external_person","supplier","employee","volunteer_profile"].forEach(f=>frappe.model.set_value(cdt,cdn,f,null));frappe.model.set_value(cdt,cdn,"beneficiary_name",null);},
 external_person:load_person,supplier:load_party,employee:load_party,volunteer_profile:load_party,
 service_item(frm,cdt,cdn){const r=locals[cdt][cdn];if(!r.service_item)return;frappe.db.get_value("Item",r.service_item,["item_name","description","stock_uom"]).then(x=>{const d=x.message||{};frappe.model.set_value(cdt,cdn,"service_description",r.service_description||d.description||d.item_name);frappe.model.set_value(cdt,cdn,"uom",r.uom||d.stock_uom);});},
 project(frm,cdt,cdn){frappe.model.set_value(cdt,cdn,"budget_line",null);frappe.model.set_value(cdt,cdn,"funding_agreement",null);},
 quantity:recalc,number_of_days:recalc,rate:recalc,daily_rate:recalc,period_rate:recalc,deduction:recalc,tax_withheld:recalc
});
function set_queries(frm){
 frm.set_query("accrual_type",()=>({filters:{active:1}}));
 frm.set_query("service_item","lines",()=>({filters:{disabled:0,is_stock_item:0,is_purchase_item:1}}));
 frm.set_query("expense_account","lines",()=>({filters:{company:frm.doc.company||"",root_type:"Expense",is_group:0}}));
 frm.set_query("payable_account","lines",()=>({filters:{company:frm.doc.company||"",root_type:"Liability",is_group:0}}));
 frm.set_query("project","lines",()=>({filters:{company:frm.doc.company||"",status:["not in",["Completed","Cancelled"]]}}));
 frm.set_query("cost_center","lines",()=>({filters:{company:frm.doc.company||"",is_group:0}}));
 frm.set_query("budget_line","lines",(doc,cdt,cdn)=>({filters:{project:locals[cdt][cdn].project||"",is_group:0,status:["!=","Inactive"]}}));
 frm.set_query("funding_agreement","lines",(doc,cdt,cdn)=>({filters:{project:locals[cdt][cdn].project||"",docstatus:1}}));
}
function apply_type_defaults(r,t){r.service_item=r.service_item||t.default_service_item;r.expense_account=r.expense_account||t.default_expense_account;r.payable_account=r.payable_account||t.default_payable_account;r.uom=r.uom||t.default_uom;}
function load_person(frm,cdt,cdn){const r=locals[cdt][cdn];if(!r.external_person)return;frappe.db.get_value("External Person",r.external_person,["full_name","identification_number","mobile_no","person_status","merged_into"]).then(x=>{const d=x.message||{};if(d.person_status!=="Active"||d.merged_into){frappe.model.set_value(cdt,cdn,"external_person",null);frappe.throw(__("Only an active, non-merged External Person can be used."));}frappe.model.set_value(cdt,cdn,"beneficiary_name",d.full_name);frappe.model.set_value(cdt,cdn,"identity_number",d.identification_number);frappe.model.set_value(cdt,cdn,"mobile_number",d.mobile_no);});}
function load_party(frm,cdt,cdn){const r=locals[cdt][cdn],map={supplier:["Supplier","supplier_name"],employee:["Employee","employee_name"],volunteer_profile:["Volunteer Profile","full_name"]};for(const f in map){if(r[f]){frappe.db.get_value(map[f][0],r[f],map[f][1]).then(x=>frappe.model.set_value(cdt,cdn,"beneficiary_name",x.message[map[f][1]]));break;}}}
function recalc(frm,cdt,cdn){const r=locals[cdt][cdn];if(!frm.doc.accrual_type)return;frappe.db.get_value("Service and Allowance Type",frm.doc.accrual_type,"calculation_method").then(x=>{const m=x.message.calculation_method;let amount=0;if(m==="Days x Daily Rate")amount=flt(r.number_of_days)*flt(r.daily_rate||r.rate);else if(m==="Fixed Amount")amount=flt(r.period_rate||r.rate);else amount=flt(r.quantity||1)*flt(r.rate);frappe.model.set_value(cdt,cdn,"gross_amount",amount);frappe.model.set_value(cdt,cdn,"net_payable",amount-flt(r.deduction)-flt(r.tax_withheld));});}
