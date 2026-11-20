from frappe.model.document import Document


class ServiceandAllowanceAccrual(Document):
    def before_insert(self):
        import frappe
        frappe.throw("Legacy DocType is closed. Use Service Allowance Accrual.")
