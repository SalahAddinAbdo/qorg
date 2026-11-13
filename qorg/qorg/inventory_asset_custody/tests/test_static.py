import ast,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
def test_python_syntax():
 for p in (ROOT/'qorg/qorg/inventory_asset_custody').rglob('*.py'): ast.parse(p.read_text())
def test_form_layouts():
 for slug in ('stock_handover','asset_custody','asset_incident','physical_verification'):
  d=json.loads((ROOT/'qorg/qorg/doctype'/slug/f'{slug}.json').read_text()); assert any(x['fieldtype']=='Column Break' for x in d['fields']); assert d['field_order']==[x['fieldname'] for x in d['fields']]
def test_child_grids():
 for slug in ('stock_handover_item','custody_accessory','incident_action','verification_item'):
  d=json.loads((ROOT/'qorg/qorg/doctype'/slug/f'{slug}.json').read_text()); assert len([x for x in d['fields'] if x.get('in_list_view')])<=8
