function qorg_direct_queries(frm){
 const linked=(frm.doc.items||[]).some(r=>r.material_request||r.material_request_item||r.purchase_order||r.po_detail);
 frm.toggle_display("qorg_direct_procurement_section",!linked);
 frm.toggle_display("qorg_direct_procurement",!linked);
 frm.toggle_display("qorg_direct_procurement_reason",!linked&&frm.doc.qorg_direct_procurement);
 frm.toggle_display("qorg_direct_approval_reference",!linked&&frm.doc.qorg_direct_procurement);
}
frappe.ui.form.on("Purchase Order",{refresh:qorg_direct_queries,items_add:qorg_direct_queries,qorg_direct_procurement:qorg_direct_queries});
frappe.ui.form.on("Purchase Invoice",{refresh:qorg_direct_queries,items_add:qorg_direct_queries,qorg_direct_procurement:qorg_direct_queries});
