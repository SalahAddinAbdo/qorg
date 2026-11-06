import frappe
from frappe import _

MANAGED_PREFIX = "QOrg "

WORKFLOWS = {
    "Procurement Process": {
        "state_field": "status",
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
    "Procurement Contract": {
        "state_field": "status",
        "states": {
            "Draft": 0,
            "Under Approval": 0,
            "Active": 1,
            "Completed": 1,
            "Terminated": 1,
        },
        "transitions": [
            ("Draft", "Under Approval", "Submit for Approval", "Contract Manager"),
            ("Under Approval", "Active", "Approve Contract", "Procurement Manager"),
            ("Active", "Completed", "Complete Contract", "Contract Manager"),
            ("Active", "Terminated", "Terminate Contract", "Procurement Manager"),
        ],
    },
}


def _ensure_role(role):
    if frappe.db.exists("Role", role):
        return
    frappe.get_doc({
        "doctype": "Role",
        "role_name": role,
        "desk_access": 0 if role == "Website User" else 1,
    }).insert(ignore_permissions=True)


def _ensure_named_master(doctype, value, candidate_fields, **extra):
    if frappe.db.exists(doctype, value):
        return
    meta = frappe.get_meta(doctype)
    values = {"doctype": doctype, **extra}
    for fieldname in candidate_fields:
        if meta.has_field(fieldname):
            values[fieldname] = value
            break
    else:
        frappe.throw(_("{0} has no supported name field for provisioning {1}.").format(doctype, value))
    frappe.get_doc(values).insert(ignore_permissions=True)


def _ensure_dependencies():
    roles = set()
    states = set()
    actions = set()
    for spec in WORKFLOWS.values():
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
    meta = frappe.get_meta(doctype)
    field = meta.get_field(fieldname)
    if not field:
        frappe.throw(_("Workflow field {0} is missing from {1}.").format(fieldname, doctype))
    if field.fieldtype == "Select":
        options = {value.strip() for value in (field.options or "").splitlines() if value.strip()}
        missing = set(states) - options
        if missing:
            frappe.throw(_("Workflow states missing from {0}.{1}: {2}").format(
                doctype, fieldname, ", ".join(sorted(missing))
            ))


def _build_workflow(doctype, spec):
    name = _workflow_name(doctype)
    _assert_state_field(doctype, spec["state_field"], spec["states"])

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

    for state, doc_status in spec["states"].items():
        doc.append("states", {
            "state": state,
            "doc_status": doc_status,
            "allow_edit": "Procurement Manager",
        })
    for source, target, action, role in spec["transitions"]:
        doc.append("transitions", {
            "state": source,
            "action": action,
            "next_state": target,
            "allowed": role,
            "allow_self_approval": 0,
        })

    if doc.is_new():
        doc.insert(ignore_permissions=True)
    else:
        doc.save(ignore_permissions=True)

    # Do not silently replace a workflow owned by an administrator or another app.
    active = frappe.db.get_value(
        "Workflow",
        {"document_type": doctype, "is_active": 1, "name": ["!=", name]},
        "name",
    )
    if active:
        frappe.throw(_("Cannot activate {0}: {1} already has active workflow {2}.").format(
            name, doctype, active
        ))

    doc.reload()
    doc.is_active = 1
    doc.save(ignore_permissions=True)


def provision_workflows():
    _ensure_dependencies()
    for doctype, spec in WORKFLOWS.items():
        _build_workflow(doctype, spec)
