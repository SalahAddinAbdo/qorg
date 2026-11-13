import frappe
from frappe.tests.utils import FrappeTestCase
from qorg.qorg.inventory_asset_custody.audit import audit_runtime_configuration
class InventoryCycleRuntimeTests(FrappeTestCase):
 def test_complete_configuration(self): self.assertTrue(audit_runtime_configuration()['passed'],audit_runtime_configuration())
 def test_no_parallel_ledgers(self): self.assertFalse([x for x in ('Inventory Ledger','Asset Ledger Entry','Stock Movement') if frappe.db.exists('DocType',x)])
 def test_settings_are_standard(self):
  for dt in ('Stock Settings','Buying Settings'):
   self.assertTrue(frappe.db.exists('DocType',dt))
  self.assertFalse(frappe.db.exists('DocType','Inventory Settings'))
