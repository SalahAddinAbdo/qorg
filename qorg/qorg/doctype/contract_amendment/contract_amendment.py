from frappe.model.document import Document
from qorg.qorg.unified_contracts.services import validate_contract_amendment, apply_contract_amendment

class ContractAmendment(Document):
    def validate(self):
        validate_contract_amendment(self)
    def before_submit(self):
        validate_contract_amendment(self, for_submit=True)
    def on_submit(self):
        apply_contract_amendment(self)
