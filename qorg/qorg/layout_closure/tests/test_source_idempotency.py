import ast
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
def read(path):return (ROOT/path).read_text()
def field_definitions():
 source=read('qorg/qorg/service_allowance/provisioning.py')
 tree=ast.parse(source)
 for node in tree.body:
  if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='CUSTOM_FIELDS' for t in node.targets):
   return ast.literal_eval(node.value)
 raise AssertionError('CUSTOM_FIELDS not found')
def test_shared_cost_source_definitions_match_runtime_reconciliation():
 rows={row['fieldname']:row for row in field_definitions()['Shared Cost Allocation Run']}
 assert rows['workflow_state']['insert_after']=='qorg_allocation_responsibility_section'
 assert rows['custom_rollback_method']['insert_after']=='qorg_rollback_section'
def test_source_and_runtime_reconciliation_use_same_anchor_names():
 source=read('qorg/qorg/layout_closure/runtime_reconciliation.py')
 assert '"workflow_state", "insert_after": "qorg_allocation_responsibility_section"' in source
 assert '"custom_rollback_method", "insert_after": "qorg_rollback_section"' in source
