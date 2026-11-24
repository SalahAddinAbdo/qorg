import ast,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
def load(slug):return json.loads((ROOT/f'qorg/qorg/doctype/{slug}/{slug}.json').read_text())
def test_all_phase_child_tables_have_structured_row_layouts():
 for slug in ('evaluation_source','rating_band','training_rule','training_need_participant','evaluation_result','calculation_log'):
  d=load(slug);types=[f['fieldtype'] for f in d['fields']]
  assert 'Section Break' in types,slug
  assert 'Column Break' in types,slug
  assert d['field_order']==[f['fieldname'] for f in d['fields']]
  visible=[f for f in d['fields'] if f.get('in_list_view')]
  assert sum(int(f.get('columns') or 0) for f in visible)<=10,slug
def test_calculated_rows_are_not_editable():
 for slug in ('evaluation_result','calculation_log'):
  d=load(slug);assert d['editable_grid']==0
  assert all(f.get('read_only') for f in d['fields'] if f['fieldtype'] not in {'Section Break','Column Break'})
def test_document_technical_fields_are_hidden_read_only():
 d=load('employee_document_record');by={f['fieldname']:f for f in d['fields']}
 for name in ('storage_provider','external_document_id','external_version_id','requires_authentication','microsoft_site_url','microsoft_drive_id','microsoft_item_id','microsoft_tenant','google_file_id','google_shared_drive_id'):
  assert by[name]['hidden']==1 and by[name]['read_only']==1
def test_document_url_and_link_hydration_exist_client_and_server():
 js=(ROOT/'qorg/public/js/employee_document_record.js').read_text();py=(ROOT/'qorg/qorg/employee_lifecycle/documents.py').read_text();ast.parse(py)
 for token in ('parse_external_document_url','document_subject_context','hydrate_document_type','hydrate_requirement','toggle_display'):
  assert token in js or token in py
 for token in ('drive.google.com','docs.google.com','.sharepoint.com','1drv.ms','_hydrate_document_record'):
  assert token in py
