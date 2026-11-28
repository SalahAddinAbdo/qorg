import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
SLUGS=(
 'activity_progress_entry','beneficiary_breakdown','asset_incident',
 'budget_period_allocation','closure_checklist_item',
 'closure_outstanding_action','committee_member',
 'applicant_screening_criterion','designation_interview_criterion',
)
def load(slug):
 return json.loads((ROOT/'qorg/qorg/doctype'/slug/f'{slug}.json').read_text())
def test_field_order_unique_and_child_grid_limits():
 for slug in SLUGS:
  d=load(slug);names=[x['fieldname'] for x in d['fields']]
  assert names==d['field_order'],slug
  assert len(names)==len(set(names)),slug
  visible=[x for x in d['fields'] if x.get('in_list_view')]
  assert len(visible)<=8,slug
  assert sum(int(x.get('columns') or 0) for x in visible)<=10,slug
def test_full_width_fields_and_row_layouts():
 d=load('asset_incident');names=[x['fieldname'] for x in d['fields']]
 assert names.index('incident_description_section')<names.index('incident_description')<names.index('assessment_section')
 for slug in ('budget_period_allocation','closure_checklist_item','closure_outstanding_action','committee_member','applicant_screening_criterion'):
  assert any(x['fieldtype']=='Section Break' for x in load(slug)['fields']),slug
def test_progress_and_beneficiary_grids_are_concise():
 p=load('activity_progress_entry');visible={x['fieldname'] for x in p['fields'] if x.get('in_list_view')}
 assert visible=={'activity','activity_code','period_actual_quantity','cumulative_actual_quantity','progress_percentage','period_status'}
 b=load('beneficiary_breakdown');visible={x['fieldname'] for x in b['fields'] if x.get('in_list_view')}
 assert visible=={'row_code','project_result','project_activity','sector','geographic_location'}
