from frappe.model.document import Document
from qorg.qorg.procurement_contracting.contract_engine import validate_framework_call_off
class FrameworkCallOff(Document):
    def validate(self): validate_framework_call_off(self)
