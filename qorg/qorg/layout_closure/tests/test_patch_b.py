import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
def all_managed():
 return list((ROOT/'qorg/qorg/doctype').glob('*/*.json'))
def test_all_child_grids_respect_limits():
 for path in all_managed():
  data=json.loads(path.read_text())
  if not data.get('istable'):continue
  visible=[x for x in data.get('fields',[]) if x.get('in_list_view')]
  assert len(visible)<=8,data.get('name')
  assert sum(int(x.get('columns') or 0) for x in visible)<=10,data.get('name')
def test_all_nontrivial_child_rows_have_sections():
 long_types={'Small Text','Long Text','Text Editor','Code','HTML','Attach','Attach Image','Table','Table MultiSelect'}
 for path in all_managed():
  data=json.loads(path.read_text());fields=data.get('fields',[])
  if not data.get('istable') or len(fields)<5:continue
  # Rows with enough complexity or long content require a section.
  complex_row=len([x for x in fields if x.get('fieldtype') not in ('Section Break','Column Break')])>=5 or any(x.get('fieldtype') in long_types for x in fields)
  if complex_row:assert any(x.get('fieldtype')=='Section Break' for x in fields),data.get('name')
def test_long_fields_are_not_followed_by_column_breaks():
 long_types={'Text Editor','Long Text','Code','HTML','Table','Table MultiSelect'}
 for path in all_managed():
  data=json.loads(path.read_text());fields=data.get('fields',[])
  for i,field in enumerate(fields):
   if field.get('fieldtype') not in long_types:continue
   boundary=next((x for x in fields[i+1:] if x.get('fieldtype') in ('Column Break','Section Break','Tab Break')),None)
   assert not boundary or boundary.get('fieldtype')!='Column Break',(data.get('name'),field.get('fieldname'))
