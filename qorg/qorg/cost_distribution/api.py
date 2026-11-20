import frappe
from qorg.qorg.cost_distribution.transfer import copy_distribution
@frappe.whitelist()
def apply_profiles(doctype,name):
 doc=frappe.get_doc(doctype,name);doc.check_permission("write");from qorg.qorg.cost_distribution.adapters.common import before_validate;before_validate(doc);doc.save();return doc.name
@frappe.whitelist()
def transfer_distribution(source_doctype,source_name,target_doctype,target_name,row_map=None):
 source=frappe.get_doc(source_doctype,source_name);target=frappe.get_doc(target_doctype,target_name);source.check_permission("read");target.check_permission("write");copy_distribution(source,target,frappe.parse_json(row_map) if isinstance(row_map,str) else (row_map or {}));target.save();return target.name

@frappe.whitelist()
def generate_stock_rows(name):
 doc=frappe.get_doc("Stock Entry",name);doc.check_permission("write")
 if doc.docstatus!=0:frappe.throw("Only a draft Stock Entry can generate distributed rows.")
 from qorg.qorg.cost_distribution.adapters.stock_entry import prepare_stock_rows
 prepare_stock_rows(doc);doc.save();return doc.name
