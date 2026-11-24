import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def test_child_layout_and_grid():
 d=json.loads((ROOT/'doctype'/'employee_clearance_item'/'employee_clearance_item.json').read_text());assert d['field_order']==[x['fieldname'] for x in d['fields']];assert sum((x.get('columns') or 0) for x in d['fields'] if x.get('in_list_view'))==10
def test_dependencies_filters_and_autofill():
 p=(ROOT/'employee_lifecycle'/'separation_clearance'/'provisioning.py').read_text();j=(ROOT.parent/'public'/'js'/'employee_separation_clearance.js').read_text();assert 'mandatory_depends_on' in p and 'fetch_from' in p and 'set_query' in j and 'active_user_query' in j
def test_report_methodology():
 py=(ROOT/'report'/'employee_clearance_status'/'employee_clearance_status.py').read_text();js=(ROOT/'report'/'employee_clearance_status'/'employee_clearance_status.js').read_text();
 for token in ['Executive','Finance and Payroll','Assets and Stock','IT and Access','sticky','summary','chart']:assert token in py
 for token in ['MultiSelectList','branches','departments','employees','group_by','overdue_only']:assert token in js
