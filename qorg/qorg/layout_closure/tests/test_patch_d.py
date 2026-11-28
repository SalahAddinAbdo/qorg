import json
import re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
LAYOUT={'Section Break','Column Break','Tab Break'}
LONG={'Text Editor','Long Text','Code','HTML','Table','Table MultiSelect'}
def doctypes():return list((ROOT/'qorg/qorg/doctype').glob('*/*.json'))
def load(path):return json.loads(path.read_text())
def test_all_doctype_paths_controllers_and_field_order_are_valid():
 for path in doctypes():
  data=load(path);expected=re.sub(r'[^a-z0-9_]+','',data['name'].lower().replace(' ','_').replace('-','_'))
  assert path.parent.name==expected and path.stem==expected,data['name']
  assert path.with_suffix('.py').exists(),data['name']
  names=[row['fieldname'] for row in data.get('fields',[])]
  assert names==data.get('field_order',[]),data['name']
  assert len(names)==len(set(names)),data['name']
def test_every_section_has_at_most_nine_operational_fields():
 for path in doctypes():
  data=load(path);fields=data.get('fields',[])
  starts=[i for i,f in enumerate(fields) if f.get('fieldtype') in ('Section Break','Tab Break')]
  if not starts or (starts and starts[0]>0):starts=[0]+starts
  for start in starts:
   end=len(fields)
   for i in range(start+1,len(fields)):
    if fields[i].get('fieldtype') in ('Section Break','Tab Break'):end=i;break
   count=sum(f.get('fieldtype') not in LAYOUT for f in fields[start:end])
   assert count<=9,(data['name'],fields[start].get('fieldname'),count)
def test_long_fields_are_full_width_and_child_grids_are_concise():
 for path in doctypes():
  data=load(path);fields=data.get('fields',[])
  for i,field in enumerate(fields):
   if field.get('fieldtype') not in LONG:continue
   boundary=next((x for x in fields[i+1:] if x.get('fieldtype') in ('Column Break','Section Break','Tab Break')),None)
   assert not boundary or boundary.get('fieldtype')!='Column Break',(data['name'],field['fieldname'])
  if data.get('istable'):
   visible=[f for f in fields if f.get('in_list_view')]
   assert len(visible)<=8,data['name']
   assert sum(int(f.get('columns') or 0) for f in visible)<=10,data['name']
