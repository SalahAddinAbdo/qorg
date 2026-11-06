import frappe
from frappe import _

def validate_purchase_invoice(doc,method=None):
    if not frappe.db.exists("DocType","Procurement and Contracting Settings"): return
    settings=frappe.get_single("Procurement and Contracting Settings")
    for row in doc.items:
        if not row.purchase_order: continue
        process=frappe.db.get_value("Procurement Award Decision",{"purchase_order":row.purchase_order,"docstatus":1},"procurement_process")
        if not process: continue
        ptype=frappe.db.get_value("Procurement Process",process,"procurement_type")
        if ptype=="Goods" and settings.require_receipt_before_goods_invoice and not row.purchase_receipt:
            frappe.throw(_("Purchase Receipt is required before invoicing goods for Purchase Order {0}").format(row.purchase_order))
        if ptype in ("Services","Consultancy") and settings.require_acceptance_before_service_invoice:
            if not frappe.db.exists("Procurement Completion and Acceptance",{"procurement_process":process,"purchase_order":row.purchase_order,"accepted":1,"docstatus":1}): frappe.throw(_("Approved service acceptance is required before invoicing Purchase Order {0}").format(row.purchase_order))
        if ptype=="Works" and settings.require_certification_before_works_invoice:
            if not frappe.db.exists("Procurement Completion and Acceptance",{"procurement_process":process,"purchase_order":row.purchase_order,"accepted":1,"docstatus":1}): frappe.throw(_("Approved works certificate is required before invoicing Purchase Order {0}").format(row.purchase_order))
