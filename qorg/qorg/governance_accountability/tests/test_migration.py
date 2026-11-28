import ast
from pathlib import Path

ROOT=Path(__file__).resolve().parents[4]
def read(path): return (ROOT/path).read_text()

def test_provisioning_creates_roles_settings_types_categories_channels_and_rules():
    source=read('qorg/qorg/governance_accountability/provisioning.py')
    for value in ('Accountability Manager','Accountability Officer','PSEA Focal Point','Whistleblowing Report','Aid Assistance','Procurement','WhatsApp','name = f"Default - {category}"'):
        assert value in source
    assert 'frappe.get_single("Accountability Settings")' in source
    assert 'insert(ignore_permissions=True)' in source
    assert 'frappe.clear_cache()' in source

def test_provisioning_does_not_insert_single_settings_document():
    source=read('qorg/qorg/governance_accountability/provisioning.py')
    assert 'frappe.get_doc({"doctype": "Accountability Settings"}).insert' not in source

def test_procurement_migration_maps_all_legacy_business_fields():
    source=read('qorg/qorg/governance_accountability/migration.py')
    for field in ('procurement_process','supplier','complaint_details','evidence','investigation_findings','decision','corrective_action','closed_on','assigned_to'):
        assert f'source.{field}' in source
    for target in ('case_details','review_summary','resolution_decision','corrective_action_summary','legacy_doctype','legacy_name','migration_version'):
        assert f'"{target}"' in source

def test_procurement_migration_is_idempotent_and_uses_per_record_savepoints():
    source=read('qorg/qorg/governance_accountability/migration.py')
    assert 'legacy_doctype": "Procurement Complaint", "legacy_name": name' in source
    assert 'frappe.db.savepoint(savepoint)' in source
    assert 'frappe.db.rollback(save_point=savepoint)' in source
    assert 'audit_procurement_migration' in source
    assert 'having count(*) > 1' in source

def test_procurement_files_move_privately_to_accountability_case():
    source=read('qorg/qorg/governance_accountability/migration.py')
    assert '"attached_to_doctype": "Accountability Case"' in source
    assert '"is_private": 1' in source
    assert 'legacy_attached_files' in source

def test_legacy_procurement_complaint_locks_only_after_migration():
    source=read('qorg/qorg/governance_accountability/legacy.py')
    assert 'lock_legacy_procurement_complaints' in source
    assert 'if doc.is_new()' in source
    assert 'legacy_doctype": "Procurement Complaint"' in source
    assert 'read only' in source

def test_hooks_order_provisioning_before_migration_and_registers_legacy_guard_once():
    hooks=read('qorg/hooks.py')
    provision='qorg.qorg.governance_accountability.provisioning.provision_governance_accountability'
    migrate='qorg.qorg.governance_accountability.migration.migrate_procurement_complaints'
    assert hooks.count(provision)==2
    assert hooks.count(migrate)==1
    after=hooks[hooks.index('after_migrate = ['):]
    assert after.index(provision) < after.index(migrate)
    assert hooks.count('qorg.qorg.governance_accountability.legacy.protect_procurement_complaint')==1

def test_governance_sources_parse():
    for path in (ROOT/'qorg/qorg/governance_accountability').rglob('*.py'):
        ast.parse(path.read_text())
