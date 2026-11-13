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
