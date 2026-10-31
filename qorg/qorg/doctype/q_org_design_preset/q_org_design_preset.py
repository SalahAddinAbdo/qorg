import json
import frappe
from frappe.model.document import Document
class QOrgDesignPreset(Document):
    def validate(self):
        if self.tokens_json:
            try: json.loads(self.tokens_json)
            except ValueError: frappe.throw("Advanced Semantic Tokens must be valid JSON.")
        if self.is_system_preset and not self.is_new():
            self.flags.ignore_links = True
