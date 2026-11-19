import frappe
from frappe import _
from frappe.model.document import Document
from qorg.qorg.shared_cost_allocation.validation import validate_rule

class SharedCostAllocationRule(Document):
    def validate(self): validate_rule(self)
    def before_update_after_submit(self): frappe.throw(_("Submitted allocation rules are immutable. Amend the rule with a new effective date."))
    def on_submit(self):
        self.db_set("status","Active",update_modified=False)
        if self.supersedes_rule:
            old=frappe.get_doc("Shared Cost Allocation Rule",self.supersedes_rule)
            old.db_set("status","Superseded",update_modified=False)
            if self.change_effective_date: old.db_set("effective_to",frappe.utils.add_days(self.change_effective_date,-1),update_modified=False)
    def on_cancel(self):
        if frappe.db.exists("Shared Cost Allocation Run",{"allocation_rule":self.name,"docstatus":1}): frappe.throw(_("Submitted allocation runs exist for this rule."))
        self.db_set("status","Cancelled",update_modified=False)
