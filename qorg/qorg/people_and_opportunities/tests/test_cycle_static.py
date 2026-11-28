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
 assert 'SAFE_DEFAULT_VISIBILITY = "Internal Only"' in source
 assert 'SAFE_DEFAULT_PAGE_SIZE = 24' in source
 assert 'Set Default Opportunity Visibility in Website Settings.' not in source
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


def test_portal_provisioning_loads_all_non_overlapping_field_sources():
 source=(ROOT/'qorg/qorg/people_and_opportunities/portal_provisioning.py').read_text()
 data_folder=ROOT/'qorg/qorg/people_and_opportunities/data'
 filenames=('portal_custom_fields.json','website_settings_custom_fields.json')
 assert 'PORTAL_CUSTOM_FIELD_FILES' in source
 for filename in filenames:
  assert filename in source
 definitions=[]
 for filename in filenames:
  payload=json.loads((data_folder/filename).read_text())
  definitions.extend(
   (doctype,row.get('fieldname'))
   for doctype,rows in payload.items()
   for row in rows
  )
 assert all(fieldname for _,fieldname in definitions)
 assert len(definitions)==len(set(definitions))
 assert 'create_custom_fields_if_changed(definitions, update=True)' in source
 assert 'frappe.clear_cache(doctype="Website Settings")' in source


def test_portal_ownership_permissions_and_private_files_are_centralized():
 hooks=(ROOT/'qorg/hooks.py').read_text()
 ownership=(ROOT/'qorg/qorg/people_and_opportunities/portal_ownership.py').read_text()
 permissions=(ROOT/'qorg/qorg/people_and_opportunities/portal_permissions.py').read_text()
 private_files=(ROOT/'qorg/qorg/people_and_opportunities/private_files.py').read_text()
 for marker in (
  'def get_external_person_for_user',
  'def assert_owned_external_person',
  'More than one External Person is linked to this user',
  'active_only',
 ):
  assert marker in ownership
 for doctype in ('External Person','Participation Application','Job Applicant'):
  assert f'"{doctype}"' in hooks
 assert 'portal_permissions.external_person_query' in hooks
 assert 'portal_permissions.participation_application_query' in hooks
 assert 'portal_permissions.job_applicant_query' in hooks
 assert 'people_and_opportunities.private_files.has_file_permission' in hooks
 assert 'PROTECTED_DOCTYPES' in private_files
 assert 'return None' in permissions


def test_portal_profile_and_application_services_use_central_ownership():
 portal_api=(ROOT/'qorg/qorg/people_and_opportunities/portal_api.py').read_text()
 services=(ROOT/'qorg/qorg/people_and_opportunities/web_form_services.py').read_text()
 assert 'assert_owned_external_person(name)' in portal_api
 assert 'get_external_person_for_user(required=True, active_only=True)' in services
 assert 'frappe.db.get_value("External Person", {"user": user}' not in services


def test_external_opportunity_delete_guard_uses_current_participation_fields():
 source=(ROOT/'qorg/qorg/people_and_opportunities/integrity.py').read_text()
 assert '("Participation Application","opportunity")' in source
 assert '("Participation Engagement","opportunity")' in source
 assert 'external_opportunity' not in source


def test_identity_normalization_and_duplicate_control_are_centralized():
 identity=(ROOT/'qorg/qorg/people_and_opportunities/identity.py').read_text()
 people=(ROOT/'qorg/qorg/people_and_opportunities/services/people.py').read_text()
 for marker in ('def normalize_email','def normalize_mobile','def normalize_identity','def validate_identity_uniqueness'):
  assert marker in identity
 assert 'validate_identity_uniqueness(doc, settings())' in people
 assert 'doc.identification_number = normalize_identity' in people
 assert 'def normalize_email' not in people


def test_profile_completeness_is_opportunity_specific():
 source=(ROOT/'qorg/qorg/people_and_opportunities/profile_completeness.py').read_text()
 portal=(ROOT/'qorg/qorg/people_and_opportunities/portal.py').read_text()
 for marker in ('require_resume','require_identification','minimum_age','requirements'):
  assert marker in source
 assert 'validate_profile_for_opportunity(person, doc)' in portal


def test_application_routing_reuses_standard_and_participation_models():
 portal=(ROOT/'qorg/qorg/people_and_opportunities/portal.py').read_text()
 assert 'behavior == "Employment"' in portal
 assert '"Job Applicant"' in portal
 assert 'behavior in ("Volunteering", "Internship")' in portal
 assert '"Participation Application"' in portal
 assert 'result["application_doctype"] = None' in portal


def test_deep_review_fixes_all_portal_entry_paths():
 workflow=(ROOT/'qorg/qorg/people_and_opportunities/web_form_workflow.py').read_text()
 services=(ROOT/'qorg/qorg/people_and_opportunities/web_form_services.py').read_text()
 portal=(ROOT/'qorg/qorg/people_and_opportunities/portal.py').read_text()
 assert '_get_external_person_for_user' not in workflow
 assert '_get_external_person_names_for_user' not in workflow
 assert 'get_external_person_for_user' in workflow
 assert 'portal_owned_reference' in workflow
 assert 'validate_profile_for_opportunity(person, opportunity_doc)' in workflow
 assert 'validate_profile_for_opportunity(person, opportunity)' in services
 assert 'behavior != "Employment"' in services
 assert 'behavior not in ("Volunteering", "Internship")' in services
 assert 'application_route_available' in portal
 assert 'result["is_open"] = False' not in portal


def test_deep_review_protects_admin_fields_files_and_requests():
 services=(ROOT/'qorg/qorg/people_and_opportunities/web_form_services.py').read_text()
 files=(ROOT/'qorg/qorg/people_and_opportunities/private_files.py').read_text()
 requests=(ROOT/'qorg/qorg/people_and_opportunities/web_form_request_security.py').read_text()
 hooks=(ROOT/'qorg/hooks.py').read_text()
 for fieldname in (
  'contact','address','employee','supplier','merged_into','person_status','source',
  'source_reference_doctype','source_reference_name','identity_verified_by',
  'identity_verified_on','payment_verified_by','payment_verified_on',
 ):
  assert f'"{fieldname}"' in services
 assert 'doc.is_private = 1' in files
 assert 'Portal users cannot move an attached file' in files
 assert 'ALLOWED_REFERENCE_DOCTYPES' in requests
 assert 'portal_owned_reference' in requests
 assert 'expires_on' in requests
 assert 'private_files.validate_sensitive_file' in hooks
 assert 'web_form_request_security.validate_web_form_request' in hooks


def test_deep_review_age_requirements_and_unicode_digits():
 profile=(ROOT/'qorg/qorg/people_and_opportunities/profile_completeness.py').read_text()
 identity=(ROOT/'qorg/qorg/people_and_opportunities/identity.py').read_text()
 assert '((current.month, current.day) < (born.month, born.day))' in profile
 assert 'minimum_age' in profile and 'maximum_age' in profile
 assert 'Date of Birth' in profile
 assert '_requirement_satisfied' in profile
 assert '_experience_years' in profile
 assert 'years_of_experience' in profile
 assert '_DIGIT_TRANSLATION' in identity
 assert '٠١٢٣٤٥٦٧٨٩' in identity
 assert '۰۱۲۳۴۵۶۷۸۹' in identity


def test_create_permissions_and_external_person_file_ownership_are_supported():
 ownership=(ROOT/'qorg/qorg/people_and_opportunities/portal_ownership.py').read_text()
 permissions=(ROOT/'qorg/qorg/people_and_opportunities/portal_permissions.py').read_text()
 acceptance=(ROOT/'qorg/qorg/people_and_opportunities/portal_acceptance.py').read_text()
 assert 'if doctype == "External Person"' in ownership
 assert permissions.count('permission_type == "create"') >= 2
 assert 'def audit_deep_runtime_configuration' in acceptance
 assert 'Duplicate External Person Users' in acceptance
 assert 'Public Protected Files' in acceptance


def test_desk_permissions_remain_configuration_driven_and_portal_only():
 permissions=(ROOT/'qorg/qorg/people_and_opportunities/portal_permissions.py').read_text()
 ownership=(ROOT/'qorg/qorg/people_and_opportunities/portal_ownership.py').read_text()
 assert 'if not is_website_user(user):\n        return ""' in permissions
 assert permissions.count('if not is_website_user(user):\n        # Continue with standard Role Permission Manager and User Permission checks.\n        return True') >= 2
 assert 'if not is_website_user(user):\n        # Frappe v16 requires an explicit truthy result from has_permission hooks.' in ownership
 assert '"System Manager" in frappe.get_roles' not in permissions
 assert '"System Manager" in frappe.get_roles' not in ownership


def test_portal_provisioning_backfills_only_required_blank_settings():
 source=(ROOT/'qorg/qorg/people_and_opportunities/portal_provisioning.py').read_text()
 assert 'def _reconcile_required_website_settings' in source
 assert 'qorg_default_opportunity_visibility' in source
 assert 'Internal Only' in source
 assert 'qorg_opportunity_portal_page_size' in source
 assert 'settings.get(fieldname) in (None, "", 0, "0")' in source
 assert 'Check fields are not' in source
