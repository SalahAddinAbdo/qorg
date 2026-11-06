from frappe.model.document import Document
from qorg.qorg.procurement_contracting.evaluation_service import calculate_financial
class FinancialEvaluation(Document):
 def validate(self): calculate_financial(self)
