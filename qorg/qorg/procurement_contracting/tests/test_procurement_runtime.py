try:
    import frappe
    from frappe.tests.utils import FrappeTestCase
except ImportError:
    frappe=None
    class FrappeTestCase: pass

class TestProcurementRuntime(FrappeTestCase):
    def setUp(self):
        if frappe is None: self.skipTest("Frappe runtime required")
    def test_required_doctypes_exist(self):
        for dt in ["Procurement Process","Procurement Notice","Supplier Registration","Procurement Submission","Technical Evaluation","Financial Evaluation","Procurement Contract","Framework Agreement","Commitment Ledger"]:
            self.assertTrue(frappe.db.exists("DocType",dt),dt)
    def test_settings_exists(self):
        self.assertTrue(frappe.db.exists("DocType", "Buying Settings"))
        self.assertTrue(frappe.db.exists("Custom Field", "Buying Settings-qorg_procurement_tab"))
