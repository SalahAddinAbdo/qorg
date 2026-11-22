from __future__ import annotations
import frappe
from qorg.qorg.enterprise_foundation.idempotent_provisioning import create_custom_fields_if_changed

COMMON = [
    {"fieldname":"qorg_movement_section","label":"QOrg Movement Governance","fieldtype":"Section Break","collapsible":1},
    {"fieldname":"qorg_movement_reason","label":"Movement Reason","fieldtype":"Small Text","reqd":1,"insert_after":"qorg_movement_section"},
    {"fieldname":"qorg_approved_reference","label":"Approved Reference","fieldtype":"Dynamic Link","options":"qorg_approved_reference_doctype","insert_after":"qorg_movement_reason"},
    {"fieldname":"qorg_approved_reference_doctype","label":"Approved Reference Type","fieldtype":"Link","options":"DocType","insert_after":"qorg_approved_reference"},
    {"fieldname":"qorg_movement_column","fieldtype":"Column Break","insert_after":"qorg_approved_reference_doctype"},
    {"fieldname":"qorg_payroll_impact","label":"Payroll Impact","fieldtype":"Check","default":"0","insert_after":"qorg_movement_column"},
    {"fieldname":"qorg_salary_structure_assignment","label":"Salary Structure Assignment","fieldtype":"Link","options":"Salary Structure Assignment","insert_after":"qorg_payroll_impact","depends_on":"eval:doc.qorg_payroll_impact"},
    {"fieldname":"qorg_funding_impact","label":"Funding Impact","fieldtype":"Check","default":"0","insert_after":"qorg_salary_structure_assignment"},
    {"fieldname":"qorg_workforce_funding_plan","label":"Workforce Funding Plan","fieldtype":"Link","options":"Workforce Funding Plan","insert_after":"qorg_funding_impact","depends_on":"eval:doc.qorg_funding_impact"},
    {"fieldname":"qorg_contract_impact","label":"Contract Impact","fieldtype":"Check","default":"0","insert_after":"qorg_workforce_funding_plan"},
    {"fieldname":"qorg_contract_amendment","label":"Contract Amendment","fieldtype":"Link","options":"Contract Amendment","insert_after":"qorg_contract_impact","depends_on":"eval:doc.qorg_contract_impact"},
    {"fieldname":"qorg_audit_section","label":"Movement Audit Snapshot","fieldtype":"Section Break","insert_after":"qorg_contract_amendment","collapsible":1},
    {"fieldname":"qorg_previous_values","label":"Previous Values","fieldtype":"Long Text","read_only":1,"insert_after":"qorg_audit_section"},
    {"fieldname":"qorg_new_values","label":"New Values","fieldtype":"Long Text","read_only":1,"insert_after":"qorg_previous_values"},
]

def provision_employee_movements():
    definitions = {dt: COMMON for dt in ("Employee Promotion", "Employee Transfer") if frappe.db.exists("DocType", dt)}
    return create_custom_fields_if_changed(definitions, update=True) if definitions else {"changed": [], "unchanged": []}
