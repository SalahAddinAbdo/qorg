from frappe.model.document import Document
from qorg.qorg.procurement_contracting.supplier_profile import validate_supplier_registration, create_or_link_supplier
class SupplierRegistration(Document):
    def validate(self): validate_supplier_registration(self)
    def on_submit(self): create_or_link_supplier(self)
