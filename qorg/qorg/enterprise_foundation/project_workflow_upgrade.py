from __future__ import annotations

import frappe

from qorg.qorg.enterprise_foundation.workflow_manager import ensure_managed_workflow


def upgrade_project_workflows(workflows: dict, actions: tuple[str,...], ensure_state, ensure_action, role_map, transitions, version="1.0.0"):
    for state in sorted({x for spec in workflows.values() for x in spec["states"]}): ensure_state(state)
    for action in actions: ensure_action(action)
    mappings=role_map()
    results={}
    for dt,spec in workflows.items():
        if not frappe.db.exists("DocType",dt): continue
        roles=mappings.get(dt) or {"owner":"System Manager","reviewer":"System Manager","approver":"System Manager"}
        states=[]
        for state in spec["states"]:
            role=roles["owner"] if state in ("Draft","Rejected") else (roles["reviewer"] if state in ("Submitted","Under Review") else roles["approver"])
            states.append({"state":state,"doc_status":0,"allow_edit":role})
        definition={"workflow_name":dt,"document_type":dt,"is_active":1,"workflow_state_field":"workflow_state","send_email_alert":0,"states":states,"transitions":transitions(spec["states"],roles)}
        results[dt]=ensure_managed_workflow(definition, version)
    frappe.clear_cache()
    return results
