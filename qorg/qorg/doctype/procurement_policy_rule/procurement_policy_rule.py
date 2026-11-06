from frappe.model.document import Document
from qorg.qorg.procurement_contracting.doctype_validators import validate_policy_rule
class ProcurementPolicyRule(Document):
    def validate(self): validate_policy_rule(self)
