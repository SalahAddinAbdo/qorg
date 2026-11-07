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

class TestProcurementIntegratedRuntime(FrappeTestCase):
    def test_material_request_estimate_and_policy_fields(self):
        mr=frappe.get_meta("Material Request");item=frappe.get_meta("Material Request Item")
        for fieldname in ("custom_estimated_procurement_value","custom_procurement_policy_rule","custom_procurement_method","custom_procurement_next_action","custom_requires_procurement_process"):
            self.assertTrue(mr.has_field(fieldname),fieldname)
        for fieldname in ("custom_estimated_unit_cost","custom_estimated_amount"):
            self.assertTrue(item.has_field(fieldname),fieldname)

    def test_procurement_web_forms_exist(self):
        for route in ("supplier-registration","tender-submission"):
            self.assertTrue(frappe.db.exists("Web Form",{"route":route,"published":1}),route)

    def test_procurement_email_templates_have_bodies(self):
        from qorg.qorg.procurement_contracting.communications import TEMPLATES
        self.assertGreaterEqual(len(TEMPLATES),15)
        for name,spec in TEMPLATES.items():
            self.assertGreater(len(spec.get("body") or ""),300,name)

    def test_procurement_child_grids_have_visible_columns(self):
        for doctype in ("Bid Summary Row","Committee Member","Contract Milestone","Eval Criterion","Eval Score","Framework Item","Framework Supplier","Guarantee Row","Commitment Entry"):
            meta=frappe.get_meta(doctype)
            visible=[df for df in meta.fields if df.in_list_view and df.fieldname!="page_break"]
            self.assertGreaterEqual(len(visible),3,doctype)
            self.assertLessEqual(len(visible),8,doctype)

class TestProcurementV2Coverage(FrappeTestCase):
    def test_all_required_email_templates(self):
        from qorg.qorg.procurement_contracting.communications import SPECS
        required={"Approved Purchase Request","Procurement Process Assignment","Procurement Invitation","Submission Deadline Reminder","Bid Submission Receipt","Supplier Information Request","Supplier Profile Approved","Supplier Profile Rejected","Bid Opening Completed","Technical Evaluation Assignment","Technical Evaluation Approved","Financial Evaluation Ready","Award Recommendation Submitted","Award Notification","Unsuccessful Bidder Notice","Contract Approval Required","Contract Activated","Contract Expiry Reminder","Guarantee Expiry Reminder","Contract Milestone Reminder","Procurement Complaint Acknowledgement","Procurement Clarification Response"}
        self.assertEqual(required,set(SPECS))

    def test_procurement_actions_are_whitelisted(self):
        from qorg.qorg.procurement_contracting import actions
        for method in (actions.create_or_open_procurement_process,actions.create_or_open_process_stage,actions.create_or_open_contract,actions.create_or_open_contract_record):
            self.assertTrue(getattr(method,"is_whitelisted",False) or hasattr(method,"__wrapped__"))

class TestProcurementPresentationAndDefaults(FrappeTestCase):
    def test_all_procurement_child_tables_have_page_break(self):
        doctypes=("Bid Summary Row","Commitment Entry","Committee Member","Contract Milestone","Eval Criterion","Eval Score","Framework Item","Framework Supplier","Guarantee Row")
        for doctype in doctypes:
            meta=frappe.get_meta(doctype)
            field=meta.get_field("page_break")
            self.assertIsNotNone(field,doctype)
            self.assertEqual(field.fieldtype,"Check",doctype)
            self.assertEqual(field.allow_on_submit,1,doctype)
            self.assertEqual(field.print_hide,1,doctype)

    def test_procurement_child_grids_show_useful_columns(self):
        doctypes=("Bid Summary Row","Commitment Entry","Committee Member","Contract Milestone","Eval Criterion","Eval Score","Framework Item","Framework Supplier","Guarantee Row")
        for doctype in doctypes:
            visible=[df for df in frappe.get_meta(doctype).fields if df.in_list_view and df.fieldname!="page_break"]
            self.assertGreaterEqual(len(visible),3,doctype)
            self.assertLessEqual(len(visible),8,doctype)

    def test_procurement_web_forms_inherit_managed_design(self):
        for route in ("supplier-registration","tender-submission"):
            name=frappe.db.get_value("Web Form",{"route":route},"name")
            self.assertTrue(name,route)
            doc=frappe.get_doc("Web Form",name)
            if doc.meta.has_field("qorg_inherit_global_web_form_design"):
                self.assertEqual(doc.qorg_inherit_global_web_form_design,1,route)
