from __future__ import annotations
import frappe
from frappe import _
from qorg.qorg.enterprise_foundation.idempotent_provisioning import create_custom_fields_if_changed

RESPONSIBLE_FIELD = "custom_current_responsible_user"
PREVIOUS_RESPONSIBLE_FIELD = "custom_previous_responsible_user"
ROUTING_FIELD = "custom_responsibility_routing"
ROUTING_OPTIONS = "\n".join(["Keep Current Responsible", "Select Next User", "Return to Previous Responsible", "Return to Document Creator", "Clear Responsibility"])


def validate_workflow_configuration(doc, method=None):
    if not doc.document_type:
        return
    keys = _mapping_keys(doc.document_type)
    for row in doc.transitions or []:
        routing = row.get(ROUTING_FIELD) or "Keep Current Responsible"
        if routing == "Select Next User":
            if not row.custom_target_role:
                frappe.throw(_("Target Role is required in transition row {0} when selecting the next user.").format(row.idx))
            if not row.custom_workflow_prompt:
                frappe.throw(_("Workflow Prompt is required in transition row {0} when selecting the next user.").format(row.idx))
        if row.custom_apply_employee_signature:
            if not row.custom_employee_signature_mapping_key:
                frappe.throw(_("Employee Signature Mapping is required in transition row {0}.").format(row.idx))
            if row.custom_employee_signature_mapping_key not in keys:
                frappe.throw(_("Signature Mapping in transition row {0} is not enabled for {1}.").format(row.idx, doc.document_type))


def ensure_current_responsible_user(doc, method=None):
    if not doc.is_active or not doc.document_type:
        return
    ensure_workflow_responsibility_fields(doc.document_type, doc.workflow_state_field)


def ensure_workflow_responsibility_fields(doctype, insert_after="workflow_state"):
    meta = frappe.get_meta(doctype)
    if meta.issingle:
        return
    fields = []
    if not meta.has_field(RESPONSIBLE_FIELD):
        fields.append({"fieldname": RESPONSIBLE_FIELD, "label": "Current Responsible User", "fieldtype": "Link", "options": "User", "insert_after": insert_after, "read_only": 1, "print_hide": 1, "allow_on_submit": 1, "no_copy": 1, "in_standard_filter": 1, "is_system_generated": 1, "module": "QOrg"})
    if not meta.has_field(PREVIOUS_RESPONSIBLE_FIELD):
        fields.append({"fieldname": PREVIOUS_RESPONSIBLE_FIELD, "label": "Previous Responsible User", "fieldtype": "Link", "options": "User", "insert_after": RESPONSIBLE_FIELD, "read_only": 1, "hidden": 1, "print_hide": 1, "allow_on_submit": 1, "no_copy": 1, "is_system_generated": 1, "module": "QOrg"})
    if fields:
        create_custom_fields_if_changed({doctype: fields}, update=True)
    for fieldname in (RESPONSIBLE_FIELD, PREVIOUS_RESPONSIBLE_FIELD):
        name = f"{doctype}-{fieldname}"
        if frappe.db.exists("Custom Field", name):
            frappe.db.set_value("Custom Field", name, {"is_system_generated": 1, "module": "QOrg"}, update_modified=False)


def provision_workflow_responsibility_routing():
    create_custom_fields_if_changed({"Workflow Transition": [{"fieldname": ROUTING_FIELD, "label": "Responsibility Routing", "fieldtype": "Select", "options": ROUTING_OPTIONS, "default": "Keep Current Responsible", "insert_after": "next_state", "reqd": 1, "in_list_view": 1, "is_system_generated": 1, "module": "QOrg", "description": "Keep Current Responsible: keep the same user. Select Next User: choose the next user manually. Return to Previous Responsible: return to the user who sent the previous handoff. Return to Document Creator: return to the document owner. Clear Responsibility: remove responsibility for a final state."}]}, update=True)
    frappe.clear_cache(doctype="Workflow Transition")
    for name in frappe.get_all("Workflow", filters={"is_active": 1}, pluck="name"):
        workflow = frappe.get_doc("Workflow", name)
        ensure_workflow_responsibility_fields(workflow.document_type, workflow.workflow_state_field)
        changed = False
        for row in workflow.transitions or []:
            if not row.get(ROUTING_FIELD):
                row.set(ROUTING_FIELD, "Select Next User" if row.get("custom_assignment_required") else "Keep Current Responsible")
                changed = True
        if changed:
            workflow.flags.ignore_validate = True
            workflow.save(ignore_permissions=True)
    for legacy in ("Workflow Transition-custom_assignment_required", "Workflow Transition-custom_target_user_field", "Workflow-custom_current_responsible_user_field"):
        if frappe.db.exists("Custom Field", legacy):
            frappe.delete_doc("Custom Field", legacy, ignore_permissions=True, force=True)
    frappe.clear_cache(doctype="Workflow Transition")


def _mapping_keys(doctype):
    if not frappe.db.exists("DocType", "Employee Signature Configuration"):
        return set()
    keys=set()
    for name in frappe.get_all("Employee Signature Configuration", filters={"enabled":1,"document_type":doctype}, pluck="name"):
        for row in frappe.get_doc("Employee Signature Configuration",name).signature_mappings or []:
            if row.enabled and row.mapping_key: keys.add(row.mapping_key)
    return keys
