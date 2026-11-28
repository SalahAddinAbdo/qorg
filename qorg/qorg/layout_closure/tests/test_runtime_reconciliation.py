import ast
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
def read(path):return (ROOT/path).read_text()
def notification_definitions():
 source=read('qorg/qorg/project_management/notification_provisioning.py')
 tree=ast.parse(source)
 for node in tree.body:
  if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='CHILD_FIELDS' for t in node.targets):
   return ast.literal_eval(node.value)
  if isinstance(node,ast.AnnAssign) and isinstance(node.target,ast.Name) and node.target.id=='CHILD_FIELDS':
   return ast.literal_eval(node.value)
 raise AssertionError('CHILD_FIELDS not found')
def test_runtime_reconciliation_is_wired_into_provisioning():
 source=read('qorg/qorg/project_management/notification_provisioning.py')
 assert 'reconcile_runtime_layouts' in source
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
 assert 'frappe.db.sql' not in source
def test_external_opportunity_has_permanent_publication_section_and_source_chain():
 data=json.loads(read('qorg/qorg/doctype/external_opportunity/external_opportunity.json'))
 names=[row['fieldname'] for row in data['fields']]
 assert names.index('application_limit')<names.index('publication_section')<names.index('dates_col_3')
 portal=json.loads(read('qorg/qorg/people_and_opportunities/data/portal_custom_fields.json'))
 rows=portal.get('External Opportunity',portal) if isinstance(portal,dict) else portal
 route=next(row for row in rows if row.get('fieldname')=='route')
 assert route['insert_after']=='publication_section'
 source=read('qorg/qorg/layout_closure/runtime_reconciliation.py')
 assert 'External Opportunity-qorg_publication_section' in source
 assert 'removed_obsolete_layout_fields' in source
def test_notification_rule_grid_sources_hide_nonessential_columns():
 definitions={row['fieldname']:row for row in notification_definitions()}
 for fieldname in ('reference_doctype','trigger_type','delivery_channel'):
  assert definitions[fieldname]['in_list_view']==0
def test_runtime_audit_is_packaged_with_reconciliation():
 source=read('qorg/qorg/layout_closure/runtime_reconciliation.py')
 assert 'def audit_runtime_layouts' in source
 assert 'checked_doctypes' in source and 'error_count' in source
