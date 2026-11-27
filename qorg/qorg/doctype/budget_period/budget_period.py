import frappe
from frappe.model.document import Document
from frappe.utils import getdate
class BudgetPeriod(Document):
    def validate(self):
        from qorg.qorg.finance_period_control.period_factory import validate_period
        validate_period(self)
        if getdate(self.from_date) > getdate(self.to_date): frappe.throw("From Date cannot be after To Date")
        overlap=frappe.db.sql("""select name from `tabBudget Period` where company=%s and name!=%s and status in ('Open','Closed') and from_date<=%s and to_date>=%s limit 1""",(self.company,self.name or '',self.to_date,self.from_date))
        if overlap: frappe.throw(f"Budget Period overlaps with {overlap[0][0]}")
        if self.carry_forward_to:
            target=frappe.get_doc("Budget Period",self.carry_forward_to)
            if target.company!=self.company:frappe.throw("Carry Forward To must belong to the same Company")
            if getdate(target.from_date)<=getdate(self.to_date):frappe.throw("Carry Forward To must start after this period")
        if self.is_default:
            frappe.db.sql("update `tabBudget Period` set is_default=0 where company=%s and name!=%s",(self.company,self.name or ''))
