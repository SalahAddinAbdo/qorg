import ast,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]

def test_cycle_python_syntax():
 for folder in ('people_and_opportunities','recruitment_extensions'):
  for p in (ROOT/'qorg/qorg'/folder).rglob('*.py'):ast.parse(p.read_text())
 ast.parse((ROOT/'qorg/hooks.py').read_text())

def test_integrity_handlers_are_registered():
 hooks=(ROOT/'qorg/hooks.py').read_text()
 for handler in (
  'qorg.qorg.people_and_opportunities.integrity.prevent_operational_delete',
  'qorg.qorg.people_and_opportunities.cycle_integrity.validate_external_person_links',
  'qorg.qorg.people_and_opportunities.cycle_integrity.validate_external_opportunity_links',
  'qorg.qorg.people_and_opportunities.cycle_integrity.validate_job_applicant_person',
 ):
  assert handler in hooks,handler

def test_delete_guards_cover_recruitment_and_participation():
 source=(ROOT/'qorg/qorg/people_and_opportunities/integrity.py').read_text()
 for marker in ('Job Applicant','Participation Application','Participation Engagement'):
  assert marker in source

def test_recruitment_template_field_is_meta_aware():
 source=(ROOT/'qorg/qorg/recruitment_extensions/notifications.py').read_text()
 assert 'def _template_body' in source
 assert 'meta.has_field("response_html")' in source
 assert '_template_body(template_doc)' in source

def test_recruitment_templates_have_valid_css():
 for p in (ROOT/'qorg/qorg/recruitment_extensions/data/email_templates').glob('*.json'):
  d=json.loads(p.read_text())
  text=json.dumps(d,ensure_ascii=False)
  assert 'background:#176b87;{' not in text,p

def test_core_doctype_dependencies_resolve():
 for slug in ('external_person','external_opportunity','recruitment_assessment_stage','recruitment_decision_log','recruitment_notification_log','work_commencement_notice'):
  p=ROOT/'qorg/qorg/doctype'/slug/f'{slug}.json'
  if not p.exists(): continue
  d=json.loads(p.read_text())
  names={x.get('fieldname') for x in d.get('fields',[])}|{'docstatus','workflow_state'}
  for field in d.get('fields',[]):
   for prop in ('depends_on','mandatory_depends_on','read_only_depends_on'):
    for ref in re.findall(r'doc\.([A-Za-z0-9_]+)',str(field.get(prop) or '')):
     assert ref in names,(p,field.get('fieldname'),prop,ref)


def test_shared_hooks_preserve_project_cycle_and_add_people_cycle():
 hooks=(ROOT/'qorg/hooks.py').read_text()
 for handler in (
  'validate_external_person_links',
  'validate_external_opportunity_links',
  'validate_job_applicant_person',
 ):
  assert hooks.count(handler)==1
 assert "'External Person':" in hooks
 assert "'External Opportunity':" in hooks
 assert "'Job Applicant':" in hooks

def test_recruitment_templates_are_operationally_linked():
 hooks=(ROOT/'qorg/hooks.py').read_text()
 source=(ROOT/'qorg/public/js/recruitment_communications.js').read_text()
 assert 'recruitment_communications.js' in hooks
 for p in (ROOT/'qorg/qorg/recruitment_extensions/data/email_templates').glob('*.json'):
  template=json.loads(p.read_text())['name']
  assert template in source,template
 assert 'preview_recruitment_message' in source
 assert 'send_managed_recruitment_message' in source

def test_recruitment_notification_methods_are_whitelisted():
 source=(ROOT/'qorg/qorg/recruitment_extensions/notifications.py').read_text()
 assert '@frappe.whitelist()\ndef preview_recruitment_message' in source
 assert '@frappe.whitelist()\ndef send_managed_recruitment_message' in source


def test_opportunity_portal_settings_are_configuration_driven():
 source=(ROOT/'qorg/qorg/people_and_opportunities/portal_settings.py').read_text()
 fields=json.loads((ROOT/'qorg/qorg/people_and_opportunities/data/website_settings_custom_fields.json').read_text())['Website Settings']
 managed={row.get('fieldname') for row in fields}
 for fieldname in (
  'qorg_opportunity_portal_enabled','qorg_public_opportunity_listing',
  'qorg_external_applications_enabled','qorg_default_opportunity_visibility',
  'qorg_show_upcoming_opportunities','qorg_show_closed_opportunities',
  'qorg_opportunity_portal_page_size',
 ):
  assert fieldname in managed
  assert fieldname in source
 assert 'DEFAULTS =' not in source
 assert 'or 24' not in source
 assert 'PAGE_SIZE_MIN = 6' in source
 assert 'PAGE_SIZE_MAX = 50' in source


def test_application_policy_preserves_disabled_check_values():
 source=(ROOT/'qorg/qorg/people_and_opportunities/web_form_services.py').read_text()
 assert 'qorg_allow_application_edit_until_closing") or 1' not in source
 assert 'qorg_lock_application_when_screening_starts") or 1' not in source
 assert 'cint(settings.get("qorg_allow_application_edit_until_closing"))' in source
 assert 'cint(settings.get("qorg_lock_application_when_screening_starts"))' in source


def test_opportunity_portal_settings_are_isolated_in_one_tab():
 fields=json.loads((ROOT/'qorg/qorg/people_and_opportunities/data/website_settings_custom_fields.json').read_text())['Website Settings']
 by_name={row['fieldname']:row for row in fields}
 assert by_name['qorg_opportunity_portal_tab']['fieldtype']=='Tab Break'
 for fieldname in ('qorg_opportunity_portal_general_section','qorg_opportunity_portal_display_section'):
  assert by_name[fieldname]['fieldtype']=='Section Break'
 for fieldname in ('qorg_opportunity_portal_general_cb','qorg_opportunity_portal_display_cb'):
  assert by_name[fieldname]['fieldtype']=='Column Break'
 assert len(by_name)==len(fields)
