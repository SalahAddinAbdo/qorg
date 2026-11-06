import frappe
from frappe.model.document import Document
from qorg.qorg.procurement_contracting.evaluation_service import rebuild_summary
class EvaluationSummary(Document):
 @frappe.whitelist()
 def rebuild(self): return rebuild_summary(self.procurement_process)
