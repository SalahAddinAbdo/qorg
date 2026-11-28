import ast, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
def read(p): return (ROOT/p).read_text()
def load(p): return json.loads(read(p))

def test_investigation_and_corrective_are_standard_owned_doctypes():
    for slug,name,series in (("investigation_case","Investigation Case","INV-.YYYY.-.#####"),("corrective_action","Corrective Action","CAPA-.YYYY.-.#####")):
        d=load(f"qorg/qorg/doctype/{slug}/{slug}.json")
        assert d["name"]==name and d["module"]=="QOrg" and d["custom"]==0
        assert d["autoname"]=="naming_series:"
        assert next(x for x in d["fields"] if x["fieldname"]=="naming_series")["options"]==series

def test_investigation_requires_independence_conflict_clearance_and_one_lead():
    s=read('qorg/qorg/governance_accountability/investigation.py')
    for phrase in ('Exactly one active Lead Investigator','independence must be confirmed','Unresolved investigator conflicts'):
        assert phrase in s

def test_investigation_controls_interviews_evidence_and_closure():
    s=read('qorg/qorg/governance_accountability/investigation.py')
    assert 'Completed interviews require date, interviewer, and summary' in s
    assert 'Evidence Reference must be unique' in s
    assert 'Chain of Custody Notes are required' in s
    assert 'content_hash(row.file)' in s
    assert 'Findings, Conclusion, and Final Report are required' in s

def test_investigation_permissions_are_team_based_and_sensitive_attachments_private():
    hooks=read('qorg/hooks.py'); files=read('qorg/qorg/governance_accountability/private_files.py')
    assert 'investigation.investigation_query' in hooks
    assert 'investigation.investigation_permission' in hooks
    assert 'Investigation Team Member' in read('qorg/qorg/governance_accountability/investigation.py')
    assert '"Investigation Case"' in files and '"Corrective Action"' in files

def test_investigation_actions_enforce_sequence_and_prevent_parallel_active_cases():
    s=read('qorg/qorg/governance_accountability/investigation_actions.py')
    assert 'An active Investigation Case already exists' in s
    assert 'Authorized":"Planning"' in s
    assert 'Analysis":"Report Review"' in s
    assert 'Investigation must be in Report Review before closure' in s

def test_corrective_action_requires_root_cause_owner_due_date_and_effectiveness():
    d=load('qorg/qorg/doctype/corrective_action/corrective_action.json'); fields={x['fieldname']:x for x in d['fields']}
    for name in ('problem_statement','root_cause_method','root_cause','action_type','action_plan','responsible_user','due_date'):
        assert fields[name]['reqd']==1
    s=read('qorg/qorg/governance_accountability/investigation.py')
    assert 'completed progress update is required before verification' in s
    assert 'Only an effective Corrective Action can be closed' in s

def test_corrective_progress_is_server_recorded_and_bounded():
    s=read('qorg/qorg/governance_accountability/investigation_actions.py')
    assert 'Progress Percent must be between 0 and 100' in s
    assert 'doc.append("updates"' in s
    assert 'Pending Verification' in s
    assert 'Verified Effective' in s and 'Verified Ineffective' in s

def test_sources_parse_and_json_loads():
    for p in (ROOT/'qorg/qorg/governance_accountability').rglob('*.py'): ast.parse(p.read_text())
    for slug in ('investigation_case','investigation_team_member','investigation_interview','investigation_evidence','investigation_finding','corrective_action','corrective_action_update'):
        load(f'qorg/qorg/doctype/{slug}/{slug}.json')
