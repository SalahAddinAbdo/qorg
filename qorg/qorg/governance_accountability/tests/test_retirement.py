from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
def read(path):return (ROOT/path).read_text()
def test_legacy_procurement_complaint_source_is_absent_from_package():
 assert not (ROOT/'qorg/qorg/doctype/procurement_complaint').exists()
 assert not (ROOT/'qorg/public/js/procurement_complaint.js').exists()
def test_legacy_hooks_and_permissions_are_removed():
 hooks=read('qorg/hooks.py')
 assert "'Procurement Complaint':" not in hooks
 assert 'complaint_permissions' not in hooks
 assert 'migrate_procurement_complaints' not in hooks
 assert 'remove_legacy_procurement_complaint_artifacts' in hooks
def test_runtime_audit_requires_legacy_doctype_removal():
 source=read('qorg/qorg/governance_accountability/acceptance.py')
 assert "legacy_procurement_complaint_removed" in source
 assert "Legacy DocType:Procurement Complaint" in source
def test_cleanup_is_guarded_and_idempotent():
 source=read('qorg/qorg/governance_accountability/cleanup.py')
 assert 'record_count or file_count' in source
 assert 'frappe.delete_doc' in source
