import ast,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
def test_python_syntax():
 for p in (ROOT/'qorg/qorg/inventory_asset_custody').rglob('*.py'): ast.parse(p.read_text())
def test_form_layouts():
 for slug in ('stock_handover','asset_custody','asset_incident','physical_verification'):
  path=ROOT/'qorg/qorg/doctype'/slug/f'{slug}.json'
  if not path.exists(): continue
  d=json.loads(path.read_text()); assert any(x['fieldtype']=='Column Break' for x in d['fields']); assert d['field_order']==[x['fieldname'] for x in d['fields']]
def test_child_grids():
 for slug in ('stock_handover_item','custody_accessory','incident_action','verification_item'):
  path=ROOT/'qorg/qorg/doctype'/slug/f'{slug}.json'
  if not path.exists(): continue
  d=json.loads(path.read_text()); assert len([x for x in d['fields'] if x.get('in_list_view')])<=8

def test_stock_handover_dependencies_and_transport_fields():
 d=json.loads((ROOT/'qorg/qorg/doctype/stock_handover/stock_handover.json').read_text())
 fields={x['fieldname']:x for x in d['fields']}
 required={
  'recipient_external_person','recipient_partner','recipient_supplier','recipient_transporter',
  'external_recipient_phone','external_recipient_capacity','external_recipient_id','authorization_attachment',
  'issue_usage_type','issue_purpose','return_expected','expected_return_date','delivery_method',
  'transport_provider','driver_name','driver_phone','vehicle_type','vehicle_number','waybill_number',
  'departure_datetime','arrival_datetime','origin_location','destination_location','delivery_condition',
  'proof_of_delivery','transport_cost','transport_cost_reference','delivery_remarks',
  'external_confirmation_method','confirmation_datetime','verified_by_employee','witness_name'
 }
 assert not (required-set(fields))
 assert "doc.recipient_type == 'Employee'" in fields['recipient_employee']['depends_on']
 assert "doc.recipient_type != 'Employee'" in fields['external_recipient_name']['depends_on']
 assert fields['recipient_signature']['label']=='External Recipient Signature'
 assert "Direct Signature" in fields['recipient_signature']['depends_on']

def test_stock_handover_item_quantity_balance_fields():
 d=json.loads((ROOT/'qorg/qorg/doctype/stock_handover_item/stock_handover_item.json').read_text())
 fields={x['fieldname']:x for x in d['fields']}
 for name in ('issued_qty','delivered_qty','received_qty','accepted_qty','rejected_qty','damaged_qty','short_qty'):
  assert name in fields
 assert fields['accepted_qty'].get('read_only')==1

def test_quality_release_and_return_services_exist():
 source=(ROOT/'qorg/qorg/inventory_asset_custody/inspection_control.py').read_text()
 for function_name in (
  'make_release_stock_entry','make_return_purchase_receipt','mark_replacement_required',
  'validate_generated_stock_entry','register_release_stock_entry','unregister_release_stock_entry',
  'validate_generated_return_receipt','register_return_purchase_receipt','unregister_return_purchase_receipt'
 ):
  assert f'def {function_name}(' in source
 assert 'custom_quarantine_warehouse' in source
 assert 'custom_accepted_warehouse' in source
 assert 'custom_rejected_warehouse' in source

def test_quality_transaction_hooks_registered():
 source=(ROOT/'qorg/hooks.py').read_text()
 for handler in (
  'validate_generated_stock_entry','register_release_stock_entry','unregister_release_stock_entry',
  'validate_generated_return_receipt','register_return_purchase_receipt','unregister_return_purchase_receipt'
 ):
  assert source.count(f'inspection_control.{handler}') == 1

def test_quality_transaction_custom_fields_declared():
 source=(ROOT/'qorg/qorg/inventory_asset_custody/custom_fields.py').read_text()
 for fieldname in ('custom_quality_inspection','custom_release_stock_entry','custom_return_purchase_receipt','custom_replacement_reference'):
  assert fieldname in source

def test_email_templates_are_raw_html_safe():
 source=(ROOT/'qorg/qorg/procurement_contracting/communications.py').read_text()
 assert 'frappe.db.set_value("Email Template"' in source
 assert 'QORG-MANAGED-COMMUNICATION-v3.0' in source
 assert 'background-color:{{{{ primary }}}}' in source
 assert 'border-bottom:4px solid {{{{ accent }}}}' in source
 assert 'if "&lt;div" in message or "&lt;table" in message or "background:{" in message' in source
 assert 'reference_doctype' in source

def test_transporter_is_independent_of_recipient():
 d=json.loads((ROOT/'qorg/qorg/doctype/stock_handover/stock_handover.json').read_text())
 fields={x['fieldname']:x for x in d['fields']}
 assert 'Transporter' not in fields['recipient_type']['options'].split('\n')
 assert fields['has_transporter']['fieldtype']=='Check'
 assert fields['recipient_transporter']['depends_on']=='eval:doc.has_transporter == 1 && doc.transport_provider_type == "Registered Transporter"'

def test_activity_reference_is_linked_to_project_cycle():
 d=json.loads((ROOT/'qorg/qorg/doctype/stock_handover/stock_handover.json').read_text())
 fields={x['fieldname']:x for x in d['fields']}
 assert fields['activity_reference']['fieldtype']=='Link'
 assert fields['activity_reference']['options']=='Workplan Activity'
 source=(ROOT/'qorg/qorg/inventory_asset_custody/custom_fields.py').read_text()
 assert "'Activity Reference','Link','Workplan Activity'" in source

def test_runtime_fieldnames_match_managed_custom_fields():
 source=(ROOT/'qorg/qorg/inventory_asset_custody/custom_fields.py').read_text()
 receipt=(ROOT/'qorg/qorg/inventory_asset_custody/receipt_control.py').read_text()
 inspection=(ROOT/'qorg/qorg/inventory_asset_custody/inspection_control.py').read_text()
 assert 'custom_receipt_inspection_required' in source
 assert 'custom_receipt_inspection_required' in receipt
 assert 'custom_inspection_required' not in receipt
 assert 'custom_detailed_findings' in source
 assert 'custom_detailed_findings' in inspection
 assert 'custom_findings' not in inspection

def test_notifications_preserve_managed_raw_html():
 for relative in ('qorg/qorg/procurement_contracting/notifications.py','qorg/qorg/inventory_asset_custody/notifications.py'):
  source=(ROOT/relative).read_text()
  assert 'frappe.db.set_value("Notification"' in source
  assert '"message": template_doc.get(body_field)' in source
