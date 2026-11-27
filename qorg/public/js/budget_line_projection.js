frappe.ui.form.on("Budget Line", {
  refresh(frm) {
    if (!frm.is_new() && !frm.doc.is_group) {
      frm.add_custom_button(__("Refresh Projection"), () => {
        frappe.call({method:"qorg.qorg.finance_period_control.projection.refresh_projection",args:{budget_line:frm.doc.name,budget_period:frm.doc.projected_budget_period},freeze:true,callback:()=>frm.reload_doc()});
      }, __("Budget"));
    }
  }
});
