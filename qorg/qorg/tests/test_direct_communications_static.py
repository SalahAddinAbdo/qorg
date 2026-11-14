import ast,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]

def test_direct_python_sources_parse():
 for rel in ('qorg/qorg/project_management/notification_provisioning.py','qorg/qorg/inventory_asset_custody/notifications.py','qorg/qorg/procurement_contracting/notifications.py'):
  ast.parse((ROOT/rel).read_text())

def test_every_email_template_json_is_bilingual_html_and_branded():
 failures=[];count=0
 for p in (ROOT/'qorg').rglob('*.json'):
  try:d=json.loads(p.read_text())
  except:continue
  docs=d if isinstance(d,list) else [d]
  for doc in docs:
   if not isinstance(doc,dict):continue
   if doc.get('doctype')!='Email Template' and 'email_template' not in p.name: continue
   count+=1;body=doc.get('response_html') or doc.get('response') or ''
   markers = ('<table',) if doc.get('name') in {'New Employee Announcement - Bilingual','Farabi Configurable Task Summary v5 Executive'} else ('<table','dir="rtl"','company_logo','custom_print_primary_color','custom_print_accent_color')
   for marker in markers:
    if marker not in body: failures.append((str(p),doc.get('name'),marker))
   if not (doc.get('subject') or '').strip():failures.append((str(p),doc.get('name'),'subject'))
 assert count>=24
 assert not failures,failures

def test_every_source_notification_has_complete_html():
 p=ROOT/'qorg/qorg/task_management/notifications.json';docs=json.loads(p.read_text())
 for doc in docs:
  assert (doc.get('subject') or '').strip()
  assert doc.get('message_type')=='HTML'
  for marker in ('<table','dir="rtl"','company_logo','custom_print_primary_color','custom_print_accent_color'):
   assert marker in doc.get('message',''),(doc['name'],marker)
 project=(ROOT/'qorg/qorg/project_management/notification_provisioning.py').read_text()
 assert '_notification_message(label, description)' in project
 assert 'custom_print_primary_color' in project
 assert 'dir="rtl"' in project

def test_no_known_malformed_patterns():
 failures=[]
 for p in (ROOT/'qorg').rglob('*'):
  if not p.is_file() or p.suffix not in {'.json','.py'} or '/tests/' in str(p):continue
  t=p.read_text(errors='ignore')
  for bad in ('background:#176b87;{','Official QOrg communication','Official QFAP communication'):
   if bad in t:failures.append((str(p),bad))
 assert not failures,failures
