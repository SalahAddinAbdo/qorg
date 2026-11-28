import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
TARGETS=(
 ('accountability_case','routing_section'),('commitment_entry','qorg_row_overview_section'),
 ('cost_distribution_row','source_section'),('employee_document_record','identity_section'),
 ('employee_document_record','verification_section'),('employee_document_requirement','scope_section'),
 ('external_person','qorg_external_roles_full_width_section'),
 ('q_org_design_system_settings','navigation_light_section'),('q_org_design_system_settings','navigation_dark_section'),
 ('service_and_allowance_accrual','qorg_overview_section'),('service_and_allowance_accrual_line','qorg_layout_section_1'),
 ('stock_handover','delivery_section'),('stock_handover_item','item_section'),
)
def load(slug):return json.loads((ROOT/'qorg/qorg/doctype'/slug/f'{slug}.json').read_text())
def segment(data,section):
 fs=data['fields'];start=next(i for i,f in enumerate(fs) if f['fieldname']==section);end=len(fs)
 for i in range(start+1,len(fs)):
  if fs[i]['fieldtype'] in ('Section Break','Tab Break'):end=i;break
 return fs[start:end]
def test_high_density_sections_are_split_and_balanced():
 for slug,section in TARGETS:
  seg=segment(load(slug),section);functional=[f for f in seg if f['fieldtype'] not in ('Section Break','Tab Break','Column Break')]
  cols=1+sum(f['fieldtype']=='Column Break' for f in seg)
  assert len(functional)<=9,(slug,section,len(functional))
  if len(functional)>=3:assert cols>=2,(slug,section,cols)
def test_generated_long_content_sections_are_full_width():
 long_types={'Text Editor','Long Text','Code','HTML','Table','Table MultiSelect','Small Text'}
 for slug,_ in TARGETS:
  fs=load(slug)['fields']
  for i,f in enumerate(fs[:-1]):
   if f['fieldtype']!='Section Break' or not f['fieldname'].startswith('qorg_') or not f['fieldname'].endswith('_section'):
    continue
   content=fs[i+1]
   if content['fieldtype'] in long_types:
    boundary=next((x for x in fs[i+2:] if x['fieldtype'] in ('Column Break','Section Break','Tab Break')),None)
    assert not boundary or boundary['fieldtype']!='Column Break',(slug,content['fieldname'])
