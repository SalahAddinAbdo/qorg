from __future__ import annotations

import frappe
from frappe import _

MANAGED_PREFIX = "QOrg "

# Contract is intentionally not provisioned here. The unified Contract model is
# shared by employment, procurement, volunteering, consultancy, funding, and
# other contractual paths. A procurement-only workflow must not be imposed on it.
WORKFLOWS = {
    "Procurement Process": {
        "state_field": "status",
        "allow_edit": "Procurement Manager",
        "states": {
            "Draft Setup": 0,
            "Setup Approved": 0,
            "Published or Invited": 0,
            "Submission Closed": 0,
            "Opening Completed": 0,
            "Technical Evaluation Approved": 0,
            "Financial Evaluation Approved": 0,
            "Combined Evaluation Completed": 0,
            "Award Approved": 0,
            "Closed": 1,
        },
        "transitions": [
            ("Draft Setup", "Setup Approved", "Approve Setup", "Procurement Manager"),
            ("Setup Approved", "Published or Invited", "Publish or Invite", "Procurement Officer"),
            ("Published or Invited", "Submission Closed", "Close Submissions", "Procurement Officer"),
            ("Submission Closed", "Opening Completed", "Complete Opening", "Bid Opening Committee Member"),
            ("Opening Completed", "Technical Evaluation Approved", "Approve Technical Evaluation", "Technical Evaluation Committee Member"),
            ("Technical Evaluation Approved", "Financial Evaluation Approved", "Approve Financial Evaluation", "Financial Evaluation Committee Member"),
            ("Financial Evaluation Approved", "Combined Evaluation Completed", "Complete Evaluation Summary", "Main Committee Member"),
            ("Combined Evaluation Completed", "Award Approved", "Approve Award", "Procurement Award Approver"),
            ("Award Approved", "Closed", "Close Process", "Procurement Manager"),
        ],
    },
    "Supplier Registration": {
        "state_field": "registration_status",
        "allow_edit": "Procurement Manager",
        "states": {
            "Draft": 0,
            "Submitted": 0,
            "Under Due Diligence": 0,
            "Approved": 1,
            "Rejected": 0,
        },
        "transitions": [
            ("Draft", "Submitted", "Submit for Review", "Website User"),
            ("Submitted", "Under Due Diligence", "Start Due Diligence", "Procurement Officer"),
            ("Under Due Diligence", "Submitted", "Request Information", "Procurement Officer"),
            ("Under Due Diligence", "Approved", "Approve Supplier", "Procurement Manager"),
            ("Under Due Diligence", "Rejected", "Reject Supplier", "Procurement Manager"),
        ],
    },
}

# These workflows belonged to the retired Procurement Contract model or to the
# earlier procurement-only use of ERPNext Contract. They must not survive after
# the unified Contract architecture is installed.
RETIRED_MANAGED_WORKFLOWS = {
    f"{MANAGED_PREFIX}Procurement Contract Workflow",
    f"{MANAGED_PREFIX}Contract Workflow",
}


def _ensure_role(role):
    if frappe.db.exists("Role", role):
        return
    frappe.get_doc(
        {
            "doctype": "Role",
            "role_name": role,
            "desk_access": 0 if role == "Website User" else 1,
        }
    ).insert(ignore_permissions=True)


def _ensure_named_master(doctype, value, candidate_fields, **extra):
    if frappe.db.exists(doctype, value):
        return
    if not frappe.db.exists("DocType", doctype):
        return

    meta = frappe.get_meta(doctype)
    values = {"doctype": doctype, **extra}
    for fieldname in candidate_fields:
        if meta.has_field(fieldname):
            values[fieldname] = value
            break
    else:
        frappe.throw(
            _("{0} has no supported name field for provisioning {1}.").format(
                doctype, value
            )
        )
    frappe.get_doc(values).insert(ignore_permissions=True)


def _ensure_dependencies():
    roles = set()
    states = set()
    actions = set()

    for doctype, spec in WORKFLOWS.items():
        if not frappe.db.exists("DocType", doctype):
            continue
        states.update(spec["states"])
        for source, target, action, role in spec["transitions"]:
            states.update((source, target))
            actions.add(action)
            roles.add(role)

    for role in sorted(roles):
        _ensure_role(role)
    for state in sorted(states):
        _ensure_named_master(
            "Workflow State",
            state,
            ("workflow_state_name", "state"),
            style="Primary",
        )
    for action in sorted(actions):
        _ensure_named_master(
            "Workflow Action Master",
            action,
            ("workflow_action_name", "action_name", "action"),
        )


def _workflow_name(doctype):
    return f"{MANAGED_PREFIX}{doctype} Workflow"


def _assert_state_field(doctype, fieldname, states):
    if not frappe.db.exists("DocType", doctype):
        return False

    meta = frappe.get_meta(doctype)
    field = meta.get_field(fieldname)
    if not field:
        frappe.throw(
            _("Workflow field {0} is missing from {1}.").format(fieldname, doctype)
        )

    if field.fieldtype == "Select":
        options = {
            value.strip()
            for value in (field.options or "").splitlines()
            if value.strip()
        }
        missing = set(states) - options
        if missing:
            frappe.throw(
                _("Workflow states missing from {0}.{1}: {2}").format(
                    doctype, fieldname, ", ".join(sorted(missing))
                )
            )
    return True


def _build_workflow(doctype, spec):
    if not frappe.db.exists("DocType", doctype):
        return
    if not _assert_state_field(doctype, spec["state_field"], spec["states"]):
        return

    name = _workflow_name(doctype)
    if frappe.db.exists("Workflow", name):
        doc = frappe.get_doc("Workflow", name)
    else:
        doc = frappe.new_doc("Workflow")
        doc.workflow_name = name

    doc.document_type = doctype
    doc.workflow_state_field = spec["state_field"]
    doc.send_email_alert = 0
    doc.is_active = 0
    doc.set("states", [])
    doc.set("transitions", [])

    allow_edit = spec.get("allow_edit", "System Manager")
    for state, doc_status in spec["states"].items():
        doc.append(
            "states",
            {
                "state": state,
                "doc_status": doc_status,
                "allow_edit": allow_edit,
            },
        )

    for source, target, action, role in spec["transitions"]:
        doc.append(
            "transitions",
            {
                "state": source,
                "action": action,
                "next_state": target,
                "allowed": role,
                "allow_self_approval": 0,
            },
        )

    if doc.is_new():
        doc.insert(ignore_permissions=True)
    else:
        doc.save(ignore_permissions=True)

    # Do not silently replace a workflow owned by an administrator or another app.
    active = frappe.db.get_value(
        "Workflow",
        {
            "document_type": doctype,
            "is_active": 1,
            "name": ["!=", name],
        },
        "name",
    )
    if active:
        frappe.throw(
            _("Cannot activate {0}: {1} already has active workflow {2}.").format(
                name, doctype, active
            )
        )

    doc.reload()
    doc.is_active = 1
    doc.save(ignore_permissions=True)


def _remove_retired_contract_workflows():
    """Remove only QOrg-managed workflows retired by the unified Contract design."""
    if not frappe.db.exists("DocType", "Workflow"):
        return

    names = set(RETIRED_MANAGED_WORKFLOWS)
    names.update(
        frappe.get_all(
            "Workflow",
            filters={"document_type": "Procurement Contract"},
            pluck="name",
        )
    )

    # Remove the old QOrg Contract workflow only when it still uses the standard
    # ERPNext status field. Do not remove an administrator-owned workflow or a
    # future unified workflow using qorg_lifecycle_status.
    names.update(
        frappe.get_all(
            "Workflow",
            filters={
                "document_type": "Contract",
                "workflow_state_field": "status",
                "name": ["like", f"{MANAGED_PREFIX}%"],
            },
            pluck="name",
        )
    )

    for name in sorted(names):
        if frappe.db.exists("Workflow", name):
            frappe.delete_doc(
                "Workflow",
                name,
                force=True,
                ignore_permissions=True,
            )


def provision_workflows():
    _remove_retired_contract_workflows()
    _ensure_dependencies()

    for doctype, spec in WORKFLOWS.items():
        if not frappe.db.exists("DocType", doctype):
            continue
        _build_workflow(doctype, spec)
