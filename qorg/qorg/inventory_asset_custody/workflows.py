from __future__ import annotations

import frappe

VALID_WORKFLOW_STYLES = {
    "",
    "Primary",
    "Info",
    "Success",
    "Warning",
    "Danger",
    "Inverse",
}

WORKFLOW_STATES = (
    ("Pending Handover", "Warning"),
    ("Acknowledged", "Success"),
    ("Discrepancy Review", "Danger"),
    ("Active Custody", "Info"),
    ("Returned", "Success"),
    ("Under Investigation", "Warning"),
    ("Decision Pending", "Warning"),
    ("Resolved", "Success"),
    ("Counting", "Info"),
    ("Recount Required", "Warning"),
    ("Pending Approval", "Warning"),
    ("Approved", "Success"),
)

FINAL_STATES = {"Acknowledged", "Returned", "Resolved", "Approved"}

WORKFLOWS = {
    "Stock Handover Approval": {
        "document_type": "Stock Handover",
        "states": (
            ("Draft", 0, "Stock User"),
            ("Pending Handover", 0, "Stock User"),
            ("Acknowledged", 1, "Stock Manager"),
            ("Discrepancy Review", 0, "Stock Manager"),
        ),
        "transitions": (
            ("Draft", "Prepare Handover", "Pending Handover", "Stock User", ""),
            ("Pending Handover", "Acknowledge", "Acknowledged", "Stock Manager", "doc.fully_acknowledged == 1"),
            ("Pending Handover", "Review Discrepancy", "Discrepancy Review", "Stock Manager", "doc.discrepancy_status == 'Open'"),
        ),
    },
    "Asset Custody Approval": {
        "document_type": "Asset Custody",
        "states": (
            ("Draft", 0, "Asset User"),
            ("Pending Handover", 0, "Asset User"),
            ("Active Custody", 1, "Asset Manager"),
            ("Returned", 1, "Asset Manager"),
        ),
        "transitions": (
            ("Draft", "Prepare Handover", "Pending Handover", "Asset User", ""),
            ("Pending Handover", "Activate Custody", "Active Custody", "Asset Manager", "doc.recipient_declaration == 1"),
            ("Active Custody", "Confirm Return", "Returned", "Asset Manager", "doc.actual_return_date"),
        ),
    },
    "Incident Resolution": {
        "document_type": "Asset Incident",
        "states": (
            ("Draft", 0, "Stock User"),
            ("Under Investigation", 0, "Stock Manager"),
            ("Decision Pending", 0, "Stock Manager"),
            ("Resolved", 1, "Stock Manager"),
        ),
        "transitions": (
            ("Draft", "Start Investigation", "Under Investigation", "Stock Manager", ""),
            ("Under Investigation", "Submit Decision", "Decision Pending", "Stock Manager", "doc.decision != 'Pending'"),
            ("Decision Pending", "Resolve", "Resolved", "Stock Manager", "doc.decision != 'Pending'"),
        ),
    },
    "Verification Approval": {
        "document_type": "Physical Verification",
        "states": (
            ("Draft", 0, "Stock User"),
            ("Counting", 0, "Stock User"),
            ("Recount Required", 0, "Stock User"),
            ("Pending Approval", 0, "Stock Manager"),
            ("Approved", 1, "Stock Manager"),
        ),
        "transitions": (
            ("Draft", "Start Counting", "Counting", "Stock User", ""),
            ("Counting", "Request Recount", "Recount Required", "Stock Manager", ""),
            ("Counting", "Submit for Approval", "Pending Approval", "Stock User", "doc.recount_required == 0"),
            ("Recount Required", "Complete Recount", "Pending Approval", "Stock User", "doc.recount_required == 0"),
            ("Pending Approval", "Approve", "Approved", "Stock Manager", "doc.snapshot_locked == 1"),
        ),
    },
}


def _ensure_workflow_state(name: str, style: str) -> None:
    if style not in VALID_WORKFLOW_STYLES:
        frappe.throw(f"Unsupported Workflow State style: {style}")

    existing = frappe.db.exists("Workflow State", name)
    if not existing:
        frappe.get_doc(
            {
                "doctype": "Workflow State",
                "workflow_state_name": name,
                "style": style,
            }
        ).insert(ignore_permissions=True)
        return

    current_style = frappe.db.get_value("Workflow State", existing, "style") or ""
    if current_style != style:
        frappe.db.set_value(
            "Workflow State",
            existing,
            "style",
            style,
            update_modified=False,
        )


def _routing_for(next_state: str) -> str:
    return "Clear Responsibility" if next_state in FINAL_STATES else "Select Next User"


def _build_workflow(name: str, definition: dict):
    workflow = frappe.new_doc("Workflow")
    workflow.workflow_name = name
    workflow.document_type = definition["document_type"]
    workflow.is_active = 1
    workflow.send_email_alert = 0
    workflow.workflow_state_field = "workflow_state"

    for state, doc_status, role in definition["states"]:
        workflow.append(
            "states",
            {
                "state": state,
                "doc_status": doc_status,
                "allow_edit": role,
            },
        )

    routing_enabled = frappe.get_meta("Workflow Transition").has_field(
        "custom_responsibility_routing"
    )
    for state, action, next_state, role, condition in definition["transitions"]:
        row = {
            "state": state,
            "action": action,
            "next_state": next_state,
            "allowed": role,
            "condition": condition,
            "allow_self_approval": 0,
        }
        if routing_enabled:
            row["custom_responsibility_routing"] = _routing_for(next_state)
        workflow.append("transitions", row)

    return workflow


def provision_workflows():
    for name, style in WORKFLOW_STATES:
        _ensure_workflow_state(name, style)

    for name, definition in WORKFLOWS.items():
        if frappe.db.exists("Workflow", name):
            continue
        _build_workflow(name, definition).insert(ignore_permissions=True)
