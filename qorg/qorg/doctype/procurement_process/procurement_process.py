import frappe
from frappe.model.document import Document
from qorg.qorg.procurement_contracting.process_engine import validate_process_setup,freeze_setup,assert_not_frozen,copy_template
class ProcurementProcess(Document):
 def validate(self): assert_not_frozen(self); validate_process_setup(self)
 def before_submit(self): freeze_setup(self)
 @frappe.whitelist()
 def load_technical_template(self): copy_template(self,self.technical_template,"Technical"); self.save(); return True
 @frappe.whitelist()
 def load_financial_template(self): copy_template(self,self.financial_template,"Financial"); self.save(); return True
