import frappe
from frappe.utils import add_days, nowdate, getdate


def daily_procurement_alerts():
    _alert_expiring_contracts()
    _alert_expiring_guarantees()
    _alert_due_evaluations()


def _todo_exists(reference_type, reference_name, allocated_to, description):
    return frappe.db.exists("ToDo", {"reference_type": reference_type, "reference_name": reference_name, "allocated_to": allocated_to, "description": description, "status": "Open"})


def _create_todo(user, reference_type, reference_name, description, priority="Medium"):
    if not user or _todo_exists(reference_type, reference_name, user, description):
        return
    frappe.get_doc({"doctype": "ToDo", "allocated_to": user, "reference_type": reference_type, "reference_name": reference_name, "description": description, "priority": priority, "status": "Open"}).insert(ignore_permissions=True)


def _alert_expiring_contracts():
    target = add_days(nowdate(), 30)
    for row in frappe.get_all("Procurement Contract", filters={"docstatus": 1, "status": "Active", "end_date": ["between", [nowdate(), target]]}, fields=["name", "contract_manager", "end_date"]):
        _create_todo(row.contract_manager, "Procurement Contract", row.name, f"Contract expires on {row.end_date}", "High")


def _alert_expiring_guarantees():
    target = add_days(nowdate(), 30)
    rows = frappe.get_all("Procurement Guarantee Row", filters={"status": "Active", "valid_to": ["between", [nowdate(), target]]}, fields=["parent", "parenttype", "valid_to"])
    for row in rows:
        manager = frappe.db.get_value(row.parenttype, row.parent, "contract_manager") if row.parenttype == "Procurement Contract" else None
        _create_todo(manager, row.parenttype, row.parent, f"Guarantee expires on {row.valid_to}", "High")


def _alert_due_evaluations():
    for row in frappe.get_all("Procurement Process", filters={"status": ["in", ["Opening Completed", "Technical Evaluation In Progress", "Technical Evaluation Approved", "Financial Evaluation In Progress"]]}, fields=["name", "technical_committee", "financial_committee", "status"]):
        mandate = row.financial_committee if row.status in ("Technical Evaluation Approved", "Financial Evaluation In Progress") else row.technical_committee
        if not mandate:
            continue
        for member in frappe.get_all("Procurement Committee Member", filters={"parent": mandate, "active": 1, "recused": 0}, pluck="user"):
            _create_todo(member, "Procurement Process", row.name, f"Procurement evaluation action required for {row.name}")
