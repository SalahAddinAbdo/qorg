from frappe.model.document import Document
from qorg.qorg.procurement_contracting.doctype_validators import validate_evaluation_template
class EvalTemplate(Document):
    def validate(self): validate_evaluation_template(self)
