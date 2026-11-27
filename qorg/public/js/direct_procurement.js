function finance_route_ui(frm){
 const inherited=!!frm.doc.qorg_route_inherited;
 if(frm.fields_dict.qorg_procurement_method){frm.set_query("qorg_procurement_method",()=>({filters:{disabled:0}}));}
 if(frm.fields_dict.qorg_procurement_process){frm.set_query("qorg_procurement_process",()=>({filters:{company:frm.doc.company||"",docstatus:["<",2]}}));}
 if(frm.fields_dict.qorg_award_decision){frm.set_query("qorg_award_decision",()=>({filters:{procurement_process:frm.doc.qorg_procurement_process||"",decision:"Approved",docstatus:1}}));}
 ["qorg_procurement_method","qorg_route_source","qorg_procurement_process","qorg_award_decision","qorg_route_approval_status","qorg_route_reason","qorg_route_approval_reference","qorg_route_approved_by","qorg_route_approved_on"].forEach(f=>frm.toggle_display(f,true));
 frm.set_df_property("qorg_route_reason","read_only",inherited?1:0);frm.set_df_property("qorg_route_approval_reference","read_only",inherited?1:0);
 if(!frm.is_new() && !inherited && frappe.user.has_role(["Procurement Manager","Procurement Award Approver","System Manager"])){
  ["Approved","Rejected"].forEach(decision=>frm.add_custom_button(__(decision),()=>frappe.call({method:"qorg.qorg.finance_period_control.procurement_route.decide",args:{doctype:frm.doctype,name:frm.doc.name,decision},callback:()=>frm.reload_doc()}),__("Route Approval")));
 }
}
["Material Request","Purchase Order","Purchase Invoice"].forEach(dt=>frappe.ui.form.on(dt,{refresh:finance_route_ui,items_add:finance_route_ui,items_remove:finance_route_ui}));
