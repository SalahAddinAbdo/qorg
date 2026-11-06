from frappe.model.document import Document
from qorg.qorg.procurement_contracting.evaluation_service import calculate_technical
class TechnicalEvaluation(Document):
 def validate(self): calculate_technical(self)
