import ast
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]


def test_python_syntax():
    paths = (
        ROOT / "qorg/qorg/recruitment_extensions/employee_cycle_integrity.py",
        ROOT / "qorg/qorg/procurement_contracting/doctype_validators.py",
        ROOT / "qorg/qorg/governance_accountability/permissions.py",
        ROOT / "qorg/qorg/governance_accountability/cleanup.py",
        ROOT / "qorg/hooks.py",
    )

    for path in paths:
        ast.parse(path.read_text(encoding="utf-8"))


def test_latest_cumulative_hooks_and_cycles_are_present():
    hooks = (ROOT / "qorg/hooks.py").read_text(encoding="utf-8")

    for marker in (
        "Project cycle integrity validation.",
        "People, opportunities and recruitment cycle integrity.",
        "Volunteer, internship and participation cycle integrity.",
        "Employee lifecycle, separation and complaint confidentiality controls.",
    ):
        assert marker in hooks

    assert "Accountability Case" in hooks
    assert "Procurement Complaint" not in hooks
    assert "prevent_incomplete_employee_exit" in hooks
    assert (
        "governance_accountability.cleanup."
        "remove_legacy_procurement_complaint_artifacts"
    ) in hooks


def test_employee_exit_checks_custody_and_handover():
    source = (
        ROOT
        / "qorg/qorg/recruitment_extensions/employee_cycle_integrity.py"
    ).read_text(encoding="utf-8")

    assert "Asset Custody" in source
    assert "Stock Handover" in source
    assert "Pending Handover" in source
    assert "Discrepancy Review" in source


def test_accountability_confidentiality_and_routing_controls():
    validation = (
        ROOT
        / "qorg/qorg/governance_accountability/validations.py"
    ).read_text(encoding="utf-8")
    permissions = (
        ROOT
        / "qorg/qorg/governance_accountability/permissions.py"
    ).read_text(encoding="utf-8")
    actions = (
        ROOT
        / "qorg/qorg/governance_accountability/actions.py"
    ).read_text(encoding="utf-8")

    for marker in (
        "Current Responsible User must be enabled",
        "Only an authorized manager may change sensitive classification or routing",
        "Resolution Decision and Closure Rationale are required",
    ):
        assert marker in validation

    assert "Confidential" in permissions
    assert "Highly Confidential" in permissions
    assert "custom_current_responsible_user" in permissions
    assert "receiving_role" in permissions
    assert "assign_case" in actions
    assert "close_case" in actions


def test_cycle4_doctype_dependencies_resolve():
    slugs = (
        "work_commencement_notice",
        "asset_custody",
        "asset_incident",
        "project_risk",
        "project_compliance_deliverable",
        "accountability_case",
    )

    for slug in slugs:
        path = ROOT / "qorg/qorg/doctype" / slug / f"{slug}.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        names = {
            row.get("fieldname")
            for row in data.get("fields", [])
        } | {"docstatus", "workflow_state"}

        for field in data.get("fields", []):
            for prop in (
                "depends_on",
                "mandatory_depends_on",
                "read_only_depends_on",
            ):
                for reference in re.findall(
                    r"doc\.([A-Za-z0-9_]+)",
                    str(field.get(prop) or ""),
                ):
                    assert reference in names, (
                        path,
                        field.get("fieldname"),
                        prop,
                        reference,
                    )


def test_internal_custody_signatures_are_removed():
    path = ROOT / "qorg/qorg/doctype/asset_custody/asset_custody.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    names = {row["fieldname"] for row in data["fields"]}

    assert not {
        "custodian_signature",
        "handover_signature",
        "return_signature",
    } & names


def test_legacy_procurement_complaint_path_is_retired():
    assert not (
        ROOT / "qorg/qorg/doctype/procurement_complaint"
    ).exists()
    assert not (
        ROOT / "qorg/public/js/procurement_complaint.js"
    ).exists()
    assert not (
        ROOT
        / "qorg/qorg/procurement_contracting/complaint_permissions.py"
    ).exists()

    dashboard = (
        ROOT
        / "qorg/qorg/doctype/procurement_process/"
        "procurement_process_dashboard.py"
    ).read_text(encoding="utf-8")

    assert "Accountability Case" in dashboard
    assert "Procurement Complaint" not in dashboard


def test_accountability_templates_replace_legacy_acknowledgement():
    template_path = (
        ROOT
        / "qorg/qorg/governance_accountability/data/"
        "email_templates.json"
    )
    templates = json.loads(template_path.read_text(encoding="utf-8"))
    names = {
        row.get("name")
        for row in templates
    }

    assert "Accountability - Case Acknowledgement - Bilingual" in names
    assert "Accountability - Case Status Update - Bilingual" in names
    assert "Accountability - Case Response - Bilingual" in names
    assert "Accountability - Case Closure - Bilingual" in names
    assert "Procurement Complaint Acknowledgement" not in names
