from __future__ import annotations
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate

class CostDistributionProfile(Document):
    def validate(self):
        if self.effective_to and getdate(self.effective_to) < getdate(self.effective_from):
            frappe.throw(_("Effective To cannot be before Effective From."))
        if not any(row.active for row in self.transaction_types):
            frappe.throw(_("At least one active Transaction Type is required."))
        active=[row for row in self.targets if row.allow_distribution]
        if not active: frappe.throw(_("At least one active distribution target is required."))
        seen=set()
        for row in active:
            key=(row.project,row.cost_center,row.budget_line,row.funding_agreement,row.donor,row.department)
            if key in seen: frappe.throw(_("Duplicate target dimensions at row {0}.").format(row.idx))
            seen.add(key)
            if frappe.db.get_value("Project",row.project,"company") != self.company:
                frappe.throw(_("Project at row {0} does not belong to Company {1}.").format(row.idx,self.company))
            if row.cost_center and frappe.db.get_value("Cost Center",row.cost_center,"company") != self.company:
                frappe.throw(_("Cost Center at row {0} does not belong to Company {1}.").format(row.idx,self.company))
            if row.budget_line and frappe.db.get_value("Budget Line",row.budget_line,"project") != row.project:
                frappe.throw(_("Budget Line at row {0} does not belong to Project {1}.").format(row.idx,row.project))
        if self.distribution_method=="Fixed Percentage":
            total=sum(flt(row.allocation_percentage) for row in active)
            if abs(total-100)>0.0001: frappe.throw(_("Active target percentages must equal 100%. Current total: {0}%.").format(total))
        self._validate_overlap()

    def _validate_overlap(self):
        filters={"name":["!=",self.name or ""],"company":self.company,"status":"Active","match_basis":self.match_basis,"docstatus":1,"effective_from":["<=",self.effective_to or "9999-12-31"]}
        for field in ("item","item_group","expense_type","expense_account","procurement_category","department","source_cost_center"):
            filters[field]=self.get(field) or ["is","not set"]
        for name in frappe.get_all("Cost Distribution Profile",filters=filters,pluck="name"):
            other=frappe.get_doc("Cost Distribution Profile",name)
            if not other.effective_to or getdate(other.effective_to)>=getdate(self.effective_from):
                if other.priority==self.priority: frappe.throw(_("Conflicting active profile {0} has the same priority and overlapping period.").format(name))

    def on_submit(self): self.db_set("status","Active",update_modified=False)
    def on_cancel(self): self.db_set("status","Cancelled",update_modified=False)
