frappe.provide('qorg.procurement');
qorg.procurement.recalculate_estimates=function(frm){let total=0;(frm.doc.items||[]).forEach(row=>{const amount=flt(row.qty)*flt(row.custom_estimated_unit_cost);if(flt(row.custom_estimated_amount)!==amount)frappe.model.set_value(row.doctype,row.name,'custom_estimated_amount',amount);total+=amount;});frm.set_value('custom_estimated_procurement_value',total);};
frappe.ui.form.on('Material Request',{refresh(frm){frm.set_intro(__('Estimated item costs determine the applied policy, method and permitted standard purchasing route.'),'blue');qorg.procurement.recalculate_estimates(frm);if(frm.doc.docstatus!==1||frm.doc.material_request_type!=='Purchase')return;frappe.call({method:'qorg.qorg.procurement_contracting.actions.get_procurement_action_state',args:{material_request:frm.doc.name}}).then(r=>{const s=r.message||{};if(s.expected_action==='Create Procurement Process'){frm.add_custom_button(s.existing_procurement_process?__('Open Procurement Process'):__('Create Procurement Process'),()=>{if(s.existing_procurement_process){frappe.set_route('Form','Procurement Process',s.existing_procurement_process);return;}frappe.call({method:'qorg.qorg.procurement_contracting.actions.create_or_open_procurement_process',args:{material_request:frm.doc.name},freeze:true}).then(x=>frappe.set_route('Form','Procurement Process',x.message));},__('Procurement'));}});},validate(frm){qorg.procurement.recalculate_estimates(frm);},items_add(frm){qorg.procurement.recalculate_estimates(frm);},items_remove(frm){qorg.procurement.recalculate_estimates(frm);}});
frappe.ui.form.on('Material Request Item',{qty(frm){qorg.procurement.recalculate_estimates(frm);},custom_estimated_unit_cost(frm){qorg.procurement.recalculate_estimates(frm);}});


qorg.procurement.sync_material_issue_context=function(frm){
 const is_issue=frm.doc.material_request_type==='Material Issue';
 const is_employee=is_issue&&frm.doc.custom_recipient_type==='Employee';
 const fields=['custom_issue_usage_type','custom_issue_purpose','custom_workplan_activity','custom_delivery_location','custom_recipient_type','custom_recipient_employee','custom_required_delivery_date','custom_return_expected','custom_expected_return_date','custom_issue_status'];
 fields.forEach(fieldname=>frm.toggle_display(fieldname,is_issue));
 frm.toggle_reqd('custom_issue_usage_type',is_issue);
 frm.toggle_reqd('custom_issue_purpose',is_issue&&!!frm.doc.custom_issue_usage_type);
 frm.toggle_reqd('custom_recipient_type',is_issue);
 frm.toggle_display('custom_recipient_employee',is_employee);
 frm.toggle_reqd('custom_recipient_employee',is_employee);
 if(!is_issue){fields.forEach(fieldname=>{if(fieldname!=='custom_issue_status'&&frm.doc[fieldname])frm.set_value(fieldname,null);});}
 if(!is_employee&&frm.doc.custom_recipient_employee)frm.set_value('custom_recipient_employee',null);
};
frappe.ui.form.on('Material Request',{
 onload_post_render(frm){qorg.procurement.sync_material_issue_context(frm);},
 material_request_type(frm){qorg.procurement.sync_material_issue_context(frm);},
 custom_recipient_type(frm){qorg.procurement.sync_material_issue_context(frm);},
 custom_issue_usage_type(frm){qorg.procurement.sync_material_issue_context(frm);}
});
