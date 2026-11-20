frappe.ui.form.on("Cost Distribution Profile",{
 setup(frm){set_queries(frm);},refresh(frm){set_queries(frm);},company(frm){frm.set_value("item",null);frm.set_value("expense_account",null);frm.set_value("source_cost_center",null);frm.clear_table("targets");frm.refresh_field("targets");set_queries(frm);},distribution_method(frm){frm.refresh_field("targets");}
});
function set_queries(frm){
 frm.set_query("expense_account",()=>({filters:{company:frm.doc.company||"",root_type:"Expense",is_group:0}}));
 frm.set_query("source_cost_center",()=>({filters:{company:frm.doc.company||"",is_group:0}}));
 frm.set_query("project","targets",()=>({filters:{company:frm.doc.company||"",status:["not in",["Completed","Cancelled"]]}}));
 frm.set_query("cost_center","targets",()=>({filters:{company:frm.doc.company||"",is_group:0}}));
 frm.set_query("budget_line","targets",(doc,cdt,cdn)=>({filters:{project:locals[cdt][cdn].project||"",is_group:0,status:["!=","Inactive"]}}));
 frm.set_query("funding_agreement","targets",(doc,cdt,cdn)=>({filters:{project:locals[cdt][cdn].project||"",docstatus:1}}));
}
