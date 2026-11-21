"""Bench integration contract. Runs on a Frappe test site after migrate."""
try:
    import frappe
    from frappe.tests import IntegrationTestCase
except Exception:
    frappe=None
    class IntegrationTestCase: pass

class TestPayrollWorkforceIntegration(IntegrationTestCase):
    def test_required_doctypes_and_custom_fields(self):
        if not frappe:return
        for doctype in ("Workforce Funding Plan","Monthly Effort Certification","Payroll Cost Policy","Payroll Allocation Run"):
            self.assertTrue(frappe.db.exists("DocType",doctype))
        self.assertTrue(frappe.get_meta("Company").has_field("custom_enable_payroll_allocation"))
        self.assertTrue(frappe.get_meta("Salary Slip").has_field("custom_payroll_allocation_run"))
