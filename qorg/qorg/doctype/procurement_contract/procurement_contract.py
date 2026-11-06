from frappe.model.document import Document
from qorg.qorg.procurement_contracting.contract_engine import validate_contract
class ProcurementContract(Document):
    def validate(self): validate_contract(self)
