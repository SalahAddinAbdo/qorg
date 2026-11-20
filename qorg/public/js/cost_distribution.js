frappe.provide("qorg.cost_distribution");
qorg.cost_distribution.setup=function(frm,source_field,distribution_field){
 if(!frm.fields_dict[distribution_field])return;
 frm.set_query("project",distribution_field,()=>({filters:{company:frm.doc.company||"",status:["not in",["Completed","Cancelled"]]}}));
 frm.set_query("cost_center",distribution_field,()=>({filters:{company:frm.doc.company||"",is_group:0}}));
 frm.set_query("budget_line",distribution_field,(doc,cdt,cdn)=>({filters:{project:locals[cdt][cdn].project||"",is_group:0,status:["!=","Inactive"]}}));
 frm.set_query("funding_agreement",distribution_field,(doc,cdt,cdn)=>({filters:{project:locals[cdt][cdn].project||"",docstatus:1}}));
 if(!frm.is_new()&&frm.doc.docstatus===0)frm.add_custom_button(__("Apply Cost Distribution"),()=>frappe.call({method:"qorg.qorg.cost_distribution.api.apply_profiles",args:{doctype:frm.doctype,name:frm.doc.name},freeze:true,callback:()=>frm.reload_doc()}),__("Cost Distribution"));
 const section=frm.fields_dict[distribution_field].wrapper.closest('.form-section');if(section)section.classList.toggle('hide',!(frm.doc[distribution_field]||[]).length);
};
qorg.cost_distribution.refresh=function(frm,distribution_field){if(frm.fields_dict[distribution_field])frm.refresh_field(distribution_field);};

frappe.ui.form.on("Cost Distribution Row",{
 project:mark_manual,cost_center:mark_manual,budget_line:mark_manual,funding_agreement:mark_manual,donor:mark_manual,department:mark_manual,
 allocation_percentage:mark_manual,allocated_quantity:mark_manual,allocated_amount:mark_manual
});
function mark_manual(frm,cdt,cdn){
 if(frm.__qorg_distribution_sync)return;
 const row=locals[cdt][cdn];
 if(row.distribution_source==="Auto Applied"||row.distribution_source==="Transferred"){
  frappe.model.set_value(cdt,cdn,"distribution_source","Manually Adjusted");
  frappe.model.set_value(cdt,cdn,"manual_override",1);
 }
}
