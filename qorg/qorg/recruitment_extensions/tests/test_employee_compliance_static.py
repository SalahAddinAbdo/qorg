import ast
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]


def test_python_syntax():
    for path in (
        ROOT / "qorg/qorg/recruitment_extensions/employee_cycle_integrity.py",
        ROOT / "qorg/qorg/procurement_contracting/doctype_validators.py",
        ROOT / "qorg/qorg/governance_accountability/permissions.py",
        ROOT / "qorg/qorg/governance_accountability/cleanup.py",
        ROOT / "qorg/hooks.py",
    ):
        ast.parse(path.read_text(encoding="utf-8"))


def test_accountability_cycle_hooks_are_current():
    hooks = (ROOT / "qorg/hooks.py").read_text(encoding="utf-8")
    assert "Accountability Case" in hooks
    assert "'Procurement Complaint':" not in hooks
    assert "governance_accountability.cleanup.remove_legacy_procurement_complaint_artifacts" in hooks
    assert "_procurement_legacy_events" not in hooks
    assert "legacy.protect_procurement_complaint" not in hooks


def test_employee_exit_checks_custody_and_handover():
    source = (ROOT / "qorg/qorg/recruitment_extensions/employee_cycle_integrity.py").read_text(encoding="utf-8")
    for marker in ("Asset Custody", "Stock Handover", "Pending Handover", "Discrepancy Review"):
        assert marker in source


def test_accountability_confidentiality_and_routing_controls():
    validation = (ROOT / "qorg/qorg/governance_accountability/validations.py").read_text(encoding="utf-8")
    permissions = (ROOT / "qorg/qorg/governance_accountability/permissions.py").read_text(encoding="utf-8")
    actions = (ROOT / "qorg/qorg/governance_accountability/actions.py").read_text(encoding="utf-8")
    for marker in (
        "Current Responsible User must be enabled",
        "Only an authorized manager may change sensitive classification or routing",
        "Resolution Decision and Closure Rationale are required",
    ):
        assert marker in validation
    for marker in ("Confidential", "Highly Confidential", "custom_current_responsible_user", "receiving_role"):
        assert marker in permissions
    assert "assign_case" in actions and "close_case" in actions


def test_cycle4_doctype_dependencies_resolve():
    for slug in (
        "work_commencement_notice", "asset_custody", "asset_incident",
        "project_risk", "project_compliance_deliverable", "accountability_case",
    ):
        path = ROOT / "qorg/qorg/doctype" / slug / f"{slug}.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        names = {row.get("fieldname") for row in data.get("fields", [])} | {"docstatus", "workflow_state"}
        for field in data.get("fields", []):
            for prop in ("depends_on", "mandatory_depends_on", "read_only_depends_on"):
                for reference in re.findall(r"doc\.([A-Za-z0-9_]+)", str(field.get(prop) or "")):
                    assert reference in names, (path, field.get("fieldname"), prop, reference)


def test_internal_custody_signatures_are_removed():
    data = json.loads((ROOT / "qorg/qorg/doctype/asset_custody/asset_custody.json").read_text(encoding="utf-8"))
    names = {row["fieldname"] for row in data["fields"]}
    assert not {"custodian_signature", "handover_signature", "return_signature"} & names


def test_legacy_procurement_complaint_path_is_retired():
    assert not (ROOT / "qorg/qorg/doctype/procurement_complaint").exists()
    assert not (ROOT / "qorg/public/js/procurement_complaint.js").exists()
    assert not (ROOT / "qorg/qorg/procurement_contracting/complaint_permissions.py").exists()
    dashboard = (ROOT / "qorg/qorg/doctype/procurement_process/procurement_process_dashboard.py").read_text(encoding="utf-8")
    assert "Accountability Case" in dashboard
    assert "Procurement Complaint" not in dashboard


def test_accountability_templates_replace_legacy_acknowledgement():
    template_path = (
        ROOT
        / "qorg/qorg/governance_accountability/data/email_templates/"
        "accountability_templates.json"
    )
    templates = json.loads(template_path.read_text(encoding="utf-8"))
    names = {row.get("name") for row in templates}
    for name in (
        "Accountability - Case Acknowledgement - Bilingual",
        "Accountability - Case Status Update - Bilingual",
        "Accountability - Case Response - Bilingual",
        "Accountability - Case Closure - Bilingual",
    ):
        assert name in names
    communication = (
        ROOT / "qorg/qorg/procurement_contracting/communications.py"
    ).read_text(encoding="utf-8")
    assert "Procurement Complaint Acknowledgement" not in communication
