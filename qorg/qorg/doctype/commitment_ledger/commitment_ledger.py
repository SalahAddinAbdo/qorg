from frappe.model.document import Document
from qorg.qorg.procurement_contracting.commitment_engine import rebuild_ledger
class CommitmentLedger(Document):
    def validate(self): rebuild_ledger(self)
