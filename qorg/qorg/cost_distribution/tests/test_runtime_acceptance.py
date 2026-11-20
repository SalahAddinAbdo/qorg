import frappe
from frappe.tests.utils import FrappeTestCase
from qorg.qorg.cost_distribution.acceptance import audit_runtime_configuration
from qorg.qorg.cost_distribution.calculations import calculate_targets

class TestCostDistributionRuntime(FrappeTestCase):
    def test_runtime_configuration(self):
        result=audit_runtime_configuration()
        self.assertTrue(result["passed"],msg=str([x for x in result["checks"] if not x["passed"]]))

    def test_no_nested_child_tables(self):
        for dt in frappe.get_all("DocType",filters={"istable":1,"module":"QOrg"},pluck="name"):
            self.assertFalse([df.fieldname for df in frappe.get_meta(dt).fields if df.fieldtype=="Table"],msg=dt)

    def test_distribution_fields_are_optional(self):
        for dt in ("Material Request","Supplier Quotation","Purchase Order","Purchase Invoice","Expense Claim","Stock Entry"):
            df=frappe.get_meta(dt).get_field("custom_cost_distributions")
            self.assertIsNotNone(df);self.assertFalse(df.reqd)
