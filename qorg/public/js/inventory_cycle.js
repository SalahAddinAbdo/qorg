(() => {
  const canCreate = (doctype) => frappe.model.can_create(doctype);
  const createAndOpen = (method, args, doctype) => frappe.call({
    method,
    args,
    freeze: true,
    callback: (r) => {
      if (!r.message) return;
      const docs = frappe.model.sync(r.message);
      const name = (docs && docs[0] && docs[0].name) || r.message.name;
      frappe.set_route("Form", doctype, name);
    }
  });

  frappe.ui.form.on("Stock Entry", {
    refresh(frm) {
      if (frm.doc.docstatus === 1 && ["Material Issue", "Material Transfer"].includes(frm.doc.purpose) && !frm.doc.custom_stock_handover && canCreate("Stock Handover")) {
        frm.add_custom_button(__("Stock Handover"), () => createAndOpen(
          "qorg.qorg.inventory_asset_custody.actions.make_stock_handover",
          { stock_entry: frm.doc.name },
          "Stock Handover"
        ), __("Create"));
      }
    }
  });

  frappe.ui.form.on("Asset Movement", {
    refresh(frm) {
      if (frm.doc.docstatus === 1 && !frm.doc.custom_asset_custody && canCreate("Asset Custody")) {
        frm.add_custom_button(__("Asset Custody"), () => createAndOpen(
          "qorg.qorg.inventory_asset_custody.actions.make_asset_custody",
          { asset_movement: frm.doc.name },
          "Asset Custody"
        ), __("Create"));
      }
    }
  });
})();

frappe.ui.form.on('Quality Inspection', {
  refresh(frm) {
    if (frm.doc.docstatus !== 1) return;
    if (['Accepted', 'Accepted with Minor Observations', 'Partially Accepted', 'Rejected'].includes(frm.doc.custom_qorg_result) && !frm.doc.custom_release_stock_entry) {
      frm.add_custom_button(__('Create Release Stock Entry'), () => {
        frappe.call({
          method: 'qorg.qorg.inventory_asset_custody.inspection_control.make_release_stock_entry',
          args: { name: frm.doc.name },
          freeze: true,
          callback: (r) => {
            if (!r.message) return;
            frappe.model.sync(r.message);
            frappe.set_route('Form', 'Stock Entry', r.message.name);
          }
        });
      }, __('Create'));
    }
    if (flt(frm.doc.custom_rejected_qty) > 0 && !frm.doc.custom_return_purchase_receipt) {
      frm.add_custom_button(__('Create Return Purchase Receipt'), () => {
        frappe.call({
          method: 'qorg.qorg.inventory_asset_custody.inspection_control.make_return_purchase_receipt',
          args: { name: frm.doc.name },
          freeze: true,
          callback: (r) => {
            if (!r.message) return;
            frappe.model.sync(r.message);
            frappe.set_route('Form', 'Purchase Receipt', r.message.name);
          }
        });
      }, __('Create'));
    }
    if (frm.doc.custom_qorg_result === 'Replacement Required' && !frm.doc.custom_replacement_reference) {
      frm.add_custom_button(__('Register Replacement Requirement'), () => {
        frappe.call({
          method: 'qorg.qorg.inventory_asset_custody.inspection_control.mark_replacement_required',
          args: { name: frm.doc.name },
          freeze: true,
          callback: (r) => {
            if (r.message) frm.reload_doc();
          }
        });
      }, __('Create'));
    }
  }
});
