from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt, getdate, now_datetime, today


def skill_gaps(employee):
    """Project designation requirements against the standard Employee Skill Map."""
    emp = frappe.get_doc("Employee", employee)
    required = _required_skills(emp.designation)
    current = _employee_skills(employee)
    rows = []
    for skill, rule in required.items():
        actual = current.get(skill, {})
        required_level = flt(rule.get("required_level"))
        current_level = flt(actual.get("proficiency"))
        rows.append({
            "skill": skill,
            "required_level": required_level,
            "current_level": current_level,
            "gap": max(0, required_level - current_level),
            "assessment_date": actual.get("evaluation_date"),
            "valid_until": actual.get("valid_until"),
            "compliant": bool(current_level >= required_level and not _expired(actual.get("valid_until"))),
        })
    return sorted(rows, key=lambda row: (-row["gap"], row["skill"]))


def create_gap_actions(employee, responsible_user, target_date, skills=None):
    frappe.get_doc("Employee", employee).check_permission("read")
    if "HR User" not in frappe.get_roles() and "HR Manager" not in frappe.get_roles() and "System Manager" not in frappe.get_roles():
        frappe.throw(_("HR role is required."), frappe.PermissionError)
    selected = set(skills or [])
    created, existing = [], []
    skill_map = frappe.db.get_value("Employee Skill Map", {"employee": employee}, "name")
    if not skill_map:
        frappe.throw(_("Employee Skill Map is required before creating competency-gap actions."))
    for gap in skill_gaps(employee):
        if gap["compliant"] or (selected and gap["skill"] not in selected):
            continue
        duplicate = frappe.db.get_value("Development Action", {"employee": employee, "source_type": "Skill Assessment", "source_doctype": "Employee Skill Map", "source_document": skill_map, "skill": gap["skill"], "status": ["not in", ["Completed", "Cancelled"]]}, "name")
        if duplicate:
            existing.append(duplicate)
            continue
        doc = frappe.get_doc({
            "doctype": "Development Action",
            "employee": employee,
            "source_type": "Skill Assessment",
            "source_doctype": "Employee Skill Map",
            "source_document": skill_map,
            "skill": gap["skill"],
            "development_need": _("Close skill gap from {0} to required level {1}.").format(gap["current_level"], gap["required_level"]),
            "action_type": "Training",
            "responsible_person": responsible_user,
            "target_date": target_date,
            "success_measure": _("Demonstrate proficiency at or above {0} through reassessment.").format(gap["required_level"]),
            "status": "Planned",
        })
        doc.insert(ignore_permissions=True)
        created.append(doc.name)
    return {"created": created, "existing": existing}


def create_appraisal_recommendation(appraisal, recommendation, values=None):
    app = frappe.get_doc("Appraisal", appraisal)
    app.check_permission("write")
    if app.get("qorg_stage") not in {"Finalized", "Closed"}:
        frappe.throw(_("Recommendations can be prepared only after the Appraisal is Finalized."))
    values = values or {}
    mapping = {
        "Promotion": "Employee Promotion",
        "Transfer": "Employee Transfer",
        "Salary Change": "Salary Structure Assignment",
        "Contract Renewal": "Contract Amendment",
        "Funding Change": "Workforce Funding Plan",
        "Training": "Development Action",
    }
    doctype = mapping.get(recommendation)
    if not doctype:
        frappe.throw(_("Unsupported recommendation."))
    recommendation_flag = {
        "Promotion": "qorg_promotion_recommended",
        "Transfer": "qorg_transfer_recommended",
        "Salary Change": "qorg_salary_recommended",
        "Contract Renewal": "qorg_contract_recommended",
        "Funding Change": "qorg_funding_recommended",
        "Training": "qorg_training_recommended",
    }[recommendation]
    if not app.get(recommendation_flag):
        frappe.throw(_("This recommendation is not selected on the Appraisal."))
    link_field = {
        "Promotion": "qorg_promotion",
        "Transfer": "qorg_transfer",
        "Salary Change": "qorg_salary_assignment",
        "Contract Renewal": "qorg_contract_amendment",
        "Funding Change": "qorg_funding_plan",
        "Training": "qorg_development_action",
    }[recommendation]
    if app.get(link_field) and frappe.db.exists(doctype, app.get(link_field)):
        return {"doctype": doctype, "name": app.get(link_field), "existing": True}
    required_values = {
        "Promotion": ("effective_date",),
        "Transfer": ("effective_date",),
        "Salary Change": ("effective_date", "salary_structure"),
        "Contract Renewal": ("effective_date",),
        "Funding Change": ("effective_date",),
        "Training": ("target_date", "responsible_person"),
    }[recommendation]
    missing = [field for field in required_values if not values.get(field)]
    if missing:
        frappe.throw(_("Required recommendation inputs: {0}.").format(", ".join(missing)))
    doc = frappe.new_doc(doctype)
    defaults = _recommendation_defaults(app, recommendation, values)
    for fieldname, value in defaults.items():
        if value not in (None, "") and doc.meta.has_field(fieldname):
            doc.set(fieldname, value)
    doc.insert(ignore_permissions=True)
    frappe.db.set_value("Appraisal", app.name, link_field, doc.name, update_modified=True)
    return {"doctype": doctype, "name": doc.name, "existing": False}


def _recommendation_defaults(app, recommendation, values):
    common = {"employee": app.employee, "qorg_approved_reference_doctype": "Appraisal", "qorg_approved_reference": app.name, "qorg_movement_reason": values.get("reason") or _("Appraisal recommendation")}
    if recommendation == "Promotion":
        common.update({"promotion_date": values.get("effective_date") or today()})
    elif recommendation == "Transfer":
        common.update({"transfer_date": values.get("effective_date") or today()})
    elif recommendation == "Salary Change":
        common.update({"from_date": values.get("effective_date") or today(), "salary_structure": values.get("salary_structure")})
    elif recommendation == "Contract Renewal":
        contract = frappe.db.get_value("Contract", {"qorg_employee": app.employee, "docstatus": ["<", 2]}, "name", order_by="start_date desc")
        common = {"contract": contract, "effective_date": values.get("effective_date") or today(), "reason": values.get("reason") or _("Appraisal renewal recommendation")}
    elif recommendation == "Funding Change":
        common.update({"effective_from": values.get("effective_date") or today(), "supersedes_plan": values.get("supersedes_plan")})
    elif recommendation == "Training":
        common = {"employee": app.employee, "source_type": "Appraisal", "source_doctype": "Appraisal", "source_document": app.name, "development_need": values.get("reason") or _("Development action from Appraisal"), "action_type": "Training", "responsible_person": values.get("responsible_person") or frappe.session.user, "target_date": values.get("target_date") or values.get("effective_date") or today(), "success_measure": values.get("success_measure") or _("Complete the approved development action."), "status": "Planned"}
    return common


def _required_skills(designation):
    if not designation or not frappe.db.exists("DocType", "Designation Skill"):
        return {}
    parent_field = "parent"
    fields = ["skill"]
    meta = frappe.get_meta("Designation Skill")
    for fieldname in ("qorg_required_level", "proficiency", "rating"):
        if meta.has_field(fieldname):
            fields.append(fieldname)
    rows = frappe.get_all("Designation Skill", filters={parent_field: designation}, fields=fields)
    return {row.skill: {"required_level": row.get("qorg_required_level") or row.get("proficiency") or row.get("rating") or 0} for row in rows}


def _employee_skills(employee):
    name = frappe.db.get_value("Employee Skill Map", {"employee": employee}, "name")
    if not name:
        return {}
    doc = frappe.get_doc("Employee Skill Map", name)
    return {row.skill: {"proficiency": row.proficiency, "evaluation_date": row.evaluation_date, "valid_until": row.get("qorg_valid_until")} for row in doc.employee_skills}


def _expired(value):
    return bool(value and getdate(value) < getdate(today()))
