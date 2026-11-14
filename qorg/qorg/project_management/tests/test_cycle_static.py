import ast,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]

def test_project_cycle_python_syntax():
 for folder in ('project_management','task_management'):
  for p in (ROOT/'qorg/qorg'/folder).rglob('*.py'):ast.parse(p.read_text())
 ast.parse((ROOT/'qorg/hooks.py').read_text())

def test_permission_scope_distinguishes_read_and_write():
 source=(ROOT/'qorg/qorg/project_management/permissions.py').read_text()
 for marker in ('READ_TYPES','WRITE_TYPES','_is_project_manager','can_implement_changes','can_manage_beneficiaries'):
  assert marker in source
 assert 'permission_type in {"submit","cancel","amend","delete","share"}' in source

def test_project_cycle_integrity_registered():
 hooks=(ROOT/'qorg/hooks.py').read_text();guard=(ROOT/'qorg/qorg/project_management/cycle_integrity.py').read_text()
 for doctype in ('Project Result','Project Indicator','Project Workplan Activity','Project Progress Update','Project Closure'):
  assert f'"{doctype}"' in hooks
 assert 'validate_project_cycle_links' in hooks
 assert 'Invalid result hierarchy' in guard
 assert 'must belong to Project' in guard

def test_notification_due_logic_and_timeline_reference():
 source=(ROOT/'qorg/qorg/project_management/notification_engine.py').read_text()
 assert 'reference_doctype=doc.doctype' in source
 assert 'reference_name=doc.name' in source
 assert 'return due < today' in source
 assert 'add_days(today,-days)' not in source

def test_task_templates_have_valid_background_css():
 for relative in ('qorg/qorg/task_management/notifications.json','qorg/qorg/task_management/scheduler.py','qorg/qorg/task_management/task_summary_email_template.json'):
  source=(ROOT/relative).read_text()
  assert 'background:{;' not in source

def test_project_doctype_dependencies_resolve():
 for p in (ROOT/'qorg/qorg/doctype').glob('project_*/*.json'):
  d=json.loads(p.read_text());names={x.get('fieldname') for x in d.get('fields',[])}|{'docstatus','workflow_state'}
  for field in d.get('fields',[]):
   for prop in ('depends_on','mandatory_depends_on','read_only_depends_on'):
    for ref in re.findall(r'doc\.([A-Za-z0-9_]+)',str(field.get(prop) or '')):
     assert ref in names,(p,field.get('fieldname'),prop,ref)

def test_all_project_permission_handlers_are_registered():
 hooks=(ROOT/'qorg/hooks.py').read_text()
 doctypes=(
  'Project Result','Project Indicator','Indicator Target Plan','Project Workplan Activity',
  'Project Progress Update','Project Risk','Project Change Request',
  'Project Compliance Deliverable','Project Beneficiary Plan','Project Closure',
 )
 for doctype in doctypes:
  assert f'"{doctype}": (' in hooks
 assert 'permission_query_conditions[_doctype]' in hooks
 assert 'has_permission[_doctype]' in hooks

def test_notification_deduplication_is_document_specific():
 source=(ROOT/'qorg/qorg/project_management/notification_engine.py').read_text()
 assert '"document_type": doc.doctype' in source
 assert '"document_name": doc.name' in source
 assert '_already_sent(user, subject, doc)' in source

def test_project_notification_rules_are_audited_after_provisioning():
 source=(ROOT/'qorg/qorg/project_management/notification_provisioning.py').read_text()
 assert 'def audit_project_notification_configuration' in source
 assert 'audit_project_notification_configuration()' in source
 assert 'notification_record' in source
