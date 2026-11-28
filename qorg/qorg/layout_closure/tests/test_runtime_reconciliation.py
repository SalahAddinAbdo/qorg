from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
def read(path):return (ROOT/path).read_text()
def test_runtime_reconciliation_is_wired_into_provisioning():
 source=read('qorg/qorg/project_management/notification_provisioning.py')
 assert 'reconcile_runtime_layouts' in source
 assert 'delivery_channel","label":"Delivery Channel"' in source
 assert '"in_list_view":0' in source
def test_runtime_reconciliation_covers_every_runtime_gap_doctype():
 source=read('qorg/qorg/layout_closure/runtime_reconciliation.py')
 for doctype in (
  'Budget Line','External Opportunity','Procurement Process','Project Change Request',
  'Project Notification Rule','Service Allowance Accrual','Shared Cost Allocation Run',
 ):
  assert f'"{doctype}"' in source
def test_existing_custom_fields_change_layout_properties_only():
 source=read('qorg/qorg/layout_closure/runtime_reconciliation.py')
 assert 'LAYOUT_PROPERTIES = ("insert_after", "in_list_view", "columns")' in source
 assert 'frappe.db.set_value' in source
 assert 'update_modified=False' in source
 assert 'frappe.delete_doc' not in source
 assert 'frappe.db.sql' not in source
def test_runtime_audit_is_packaged_with_reconciliation():
 source=read('qorg/qorg/layout_closure/runtime_reconciliation.py')
 assert 'def audit_runtime_layouts' in source
 assert 'checked_doctypes' in source
 assert 'child_tables' in source
 assert 'error_count' in source
