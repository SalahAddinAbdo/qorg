from __future__ import annotations

import frappe

STANDARD_DOCTYPES = (
    "Company", "Fiscal Year", "Account", "Cost Center", "Accounting Dimension",
    "Budget", "Project", "Material Request", "Purchase Order", "Purchase Receipt",
    "Purchase Invoice", "Payment Entry", "Journal Entry", "Expense Claim",
    "Stock Entry", "Asset", "Payroll Entry", "Salary Slip", "GL Entry",
    "Payment Ledger Entry", "Bank Transaction",
)

QORG_DOCTYPES = (
    "Budget Line", "Donor", "Donor Type", "Project Funding Source",
    "Project Change Request", "Project Closure", "Project Workplan Activity",
    "Project Result", "Project Compliance Deliverable",
)

TRANSACTION_DOCTYPES = (
    "Material Request", "Purchase Order", "Purchase Receipt", "Purchase Invoice",
    "Payment Entry", "Journal Entry", "Expense Claim", "Stock Entry", "Asset",
    "Payroll Entry", "Salary Slip", "GL Entry",
)

EXPECTED_REPORTS = (
    "Project Budget", "Budget Versus Actual", "Budget Commitments",
    "Enhanced General Ledger", "Contract Commitments", "Milestone Payments",
)


def _field(meta, fieldname):
    field = meta.get_field(fieldname)
    if not field:
        return None
    return {
        "fieldtype": field.fieldtype,
        "options": field.options,
        "reqd": int(field.reqd or 0),
        "read_only": int(field.read_only or 0),
        "hidden": int(field.hidden or 0),
        "in_list_view": int(field.in_list_view or 0),
    }


def _dimension_record():
    name = frappe.db.get_value("Accounting Dimension", {"document_type": "Budget Line"}, "name")
    if not name:
        return None
    doc = frappe.get_doc("Accounting Dimension", name)
    return {
        "name": doc.name,
        "document_type": doc.document_type,
        "fieldname": doc.fieldname,
        "disabled": int(doc.disabled or 0),
        "dimension_defaults": [row.as_dict() for row in (doc.dimension_defaults or [])],
    }


def _doctype_snapshot(doctype):
    if not frappe.db.exists("DocType", doctype):
        return {"exists": False}
    meta = frappe.get_meta(doctype)
    return {
        "exists": True,
        "module": meta.module,
        "is_submittable": int(meta.is_submittable or 0),
        "istable": int(meta.istable or 0),
        "issingle": int(meta.issingle or 0),
        "is_tree": int(meta.is_tree or 0),
        "project": _field(meta, "project"),
        "cost_center": _field(meta, "cost_center"),
        "budget_line": _field(meta, "budget_line"),
        "company": _field(meta, "company"),
        "currency": _field(meta, "currency"),
        "posting_date": _field(meta, "posting_date"),
        "docstatus": _field(meta, "docstatus"),
        "table_fields": [
            {"fieldname": f.fieldname, "options": f.options}
            for f in meta.fields if f.fieldtype == "Table"
        ],
    }


def _child_dimension_coverage(doctype):
    if not frappe.db.exists("DocType", doctype):
        return []
    meta = frappe.get_meta(doctype)
    coverage = []
    for field in meta.fields:
        if field.fieldtype != "Table" or not field.options or not frappe.db.exists("DocType", field.options):
            continue
        child = frappe.get_meta(field.options)
        coverage.append({
            "table_field": field.fieldname,
            "child_doctype": field.options,
            "project": bool(child.get_field("project")),
            "cost_center": bool(child.get_field("cost_center")),
            "budget_line": bool(child.get_field("budget_line")),
        })
    return coverage


def audit_runtime_configuration():
    standard = {name: _doctype_snapshot(name) for name in STANDARD_DOCTYPES}
    qorg = {name: _doctype_snapshot(name) for name in QORG_DOCTYPES}
    transactions = {
        name: {
            "parent": _doctype_snapshot(name),
            "children": _child_dimension_coverage(name),
        }
        for name in TRANSACTION_DOCTYPES
    }
    missing_reports = [name for name in EXPECTED_REPORTS if not frappe.db.exists("Report", name)]
    missing_standard = [name for name, value in standard.items() if not value["exists"]]
    missing_qorg = [name for name, value in qorg.items() if not value["exists"]]
    dimension = _dimension_record()
    gl_budget_line = bool(standard.get("GL Entry", {}).get("budget_line"))

    findings = []
    if not dimension:
        findings.append("Budget Line is not registered as an Accounting Dimension.")
    elif dimension["disabled"]:
        findings.append("Budget Line Accounting Dimension is disabled.")
    if not gl_budget_line:
        findings.append("GL Entry does not expose budget_line in current Meta.")
    for doctype, snapshot in transactions.items():
        parent_has = bool(snapshot["parent"].get("budget_line"))
        child_has = any(row["budget_line"] for row in snapshot["children"])
        if not parent_has and not child_has:
            findings.append(f"{doctype} has no Budget Line field on parent or child Meta.")

    return {
        "site": frappe.local.site,
        "versions": frappe.get_versions(),
        "budget_line_dimension": dimension,
        "standard_doctypes": standard,
        "qorg_doctypes": qorg,
        "transaction_dimension_coverage": transactions,
        "missing_standard_doctypes": missing_standard,
        "missing_qorg_doctypes": missing_qorg,
        "missing_reports": missing_reports,
        "findings": findings,
        "passed_core_dimension_check": bool(dimension and not dimension["disabled"] and gl_budget_line),
    }
