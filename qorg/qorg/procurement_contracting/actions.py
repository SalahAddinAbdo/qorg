import frappe
from frappe import _


PROCESS_STAGES = {
    "Procurement Notice": {
        "field": "procurement_process",
        "states": ["Setup Approved", "Published or Invited"],
    },
    "Procurement Bid Opening": {
        "field": "procurement_process",
        "states": ["Submission Closed", "Opening Completed"],
    },
    "Bid Precheck": {
        "field": "procurement_process",
        "states": ["Opening Completed"],
    },
    "Technical Evaluation": {
        "field": "procurement_process",
        "states": ["Opening Completed", "Technical Evaluation Approved"],
    },
    "Financial Evaluation": {
        "field": "procurement_process",
        "states": ["Technical Evaluation Approved", "Financial Evaluation Approved"],
    },
    "Evaluation Summary": {
        "field": "procurement_process",
        "states": ["Financial Evaluation Approved", "Combined Evaluation Completed"],
    },
    "Award Recommendation": {
        "field": "procurement_process",
        "states": ["Combined Evaluation Completed"],
    },
    "Award Decision": {
        "field": "procurement_process",
        "states": ["Combined Evaluation Completed", "Award Approved"],
    },
    "Procurement Contract": {
        "field": "procurement_process",
        "states": ["Award Approved", "Closed"],
    },
}


def _submitted_mr(name):
    doc = frappe.get_doc("Material Request", name)
    doc.check_permission("read")

    if doc.docstatus != 1 or doc.material_request_type != "Purchase":
        frappe.throw(_("A submitted Purchase Material Request is required."))

    doc.run_method("validate")
    return doc


def _has_submitted_rfq(material_request):
    return bool(
        frappe.db.exists(
            "Request for Quotation Item",
            {
                "material_request": material_request,
                "parenttype": "Request for Quotation",
                "docstatus": 1,
            },
        )
    )


def validate_standard_buying_action(material_request, requested_action):
    """Enforce the procurement route selected by the applied policy.

    A policy routed to the managed Procurement Process cannot bypass that cycle
    through a standard RFQ or a direct Purchase Order. A standard RFQ route may
    proceed to Purchase Order only after a submitted RFQ exists for the Material
    Request. Direct Purchase Order routes remain available without an RFQ.
    """
    doc = _submitted_mr(material_request)
    expected_action = doc.get("custom_procurement_next_action")

    supported_actions = {
        "Create Procurement Process",
        "Create RFQ",
        "Create Purchase Order",
    }
    if requested_action not in {"Create RFQ", "Create Purchase Order"}:
        frappe.throw(_("Unsupported standard buying action: {0}").format(requested_action))

    if expected_action not in supported_actions:
        frappe.throw(
            _(
                "Material Request {0} does not have a valid procurement action. "
                "Revalidate the Material Request before continuing."
            ).format(doc.name)
        )

    if expected_action == "Create Procurement Process":
        frappe.throw(
            _(
                "Material Request {0} must continue through a Procurement Process "
                "and cannot use the standard {1} route."
            ).format(doc.name, requested_action)
        )

    if requested_action == "Create RFQ" and expected_action != "Create RFQ":
        frappe.throw(
            _(
                "The applied procurement policy for Material Request {0} requires "
                "{1}, not a Request for Quotation."
            ).format(doc.name, expected_action)
        )

    if requested_action == "Create Purchase Order":
        if expected_action == "Create Purchase Order":
            return

        if expected_action == "Create RFQ" and _has_submitted_rfq(doc.name):
            return

        frappe.throw(
            _(
                "A submitted Request for Quotation is required before creating a "
                "Purchase Order for Material Request {0}."
            ).format(doc.name)
        )


@frappe.whitelist()
def get_procurement_action_state(material_request):
    doc = _submitted_mr(material_request)
    existing = frappe.db.get_value(
        "Procurement Process",
        {"material_request": doc.name, "docstatus": ["<", 2]},
        "name",
    )
    return {
        "expected_action": doc.custom_procurement_next_action,
        "existing_procurement_process": existing,
        "policy_rule": doc.custom_procurement_policy_rule,
        "procurement_method": doc.custom_procurement_method,
        "estimated_value": doc.custom_estimated_procurement_value,
    }


@frappe.whitelist()
def create_or_open_procurement_process(material_request):
    doc = _submitted_mr(material_request)
    if doc.custom_procurement_next_action != "Create Procurement Process":
        frappe.throw(_("The applied procurement policy does not permit a Procurement Process."))

    existing = frappe.db.get_value(
        "Procurement Process",
        {"material_request": doc.name, "docstatus": ["<", 2]},
        "name",
    )
    if existing:
        return existing

    if not frappe.has_permission("Procurement Process", "create"):
        frappe.throw(_("Not permitted to create Procurement Process."), frappe.PermissionError)

    process = frappe.get_doc(
        {
            "doctype": "Procurement Process",
            "material_request": doc.name,
            "company": doc.company,
            "project": doc.project,
            "currency": frappe.get_cached_value("Company", doc.company, "default_currency"),
            "estimated_value": doc.custom_estimated_procurement_value,
            "procurement_type": doc.custom_procurement_type,
            "policy_rule": doc.custom_procurement_policy_rule,
            "procurement_method": doc.custom_procurement_method,
            "title": doc.title or doc.name,
        }
    )
    process.insert()
    return process.name


@frappe.whitelist()
def create_or_open_process_stage(process_name, target_doctype, defaults=None):
    if target_doctype not in PROCESS_STAGES:
        frappe.throw(_("Unsupported procurement stage."))

    process = frappe.get_doc("Procurement Process", process_name)
    process.check_permission("read")
    spec = PROCESS_STAGES[target_doctype]

    if process.status not in spec["states"]:
        frappe.throw(
            _("{0} cannot be created while the process is in {1}.").format(
                target_doctype, process.status
            )
        )

    if not frappe.has_permission(target_doctype, "create"):
        frappe.throw(
            _("Not permitted to create {0}.").format(target_doctype),
            frappe.PermissionError,
        )

    values = {"doctype": target_doctype, spec["field"]: process.name}
    if defaults:
        if isinstance(defaults, str):
            defaults = frappe.parse_json(defaults)
        values.update(
            {
                key: value
                for key, value in defaults.items()
                if frappe.get_meta(target_doctype).has_field(key)
            }
        )

    unique = {spec["field"]: process.name, "docstatus": ["<", 2]}
    if values.get("submission"):
        unique["submission"] = values["submission"]

    existing = frappe.db.get_value(target_doctype, unique, "name")
    if existing:
        return existing

    doc = frappe.get_doc(values)
    doc.insert()
    return doc.name


@frappe.whitelist()
def create_or_open_contract(award_decision):
    award = frappe.get_doc("Award Decision", award_decision)
    award.check_permission("read")

    if award.decision != "Approved":
        frappe.throw(_("The award decision must be Approved before contract creation."))

    existing = frappe.db.get_value(
        "Procurement Contract",
        {"award_decision": award.name, "docstatus": ["<", 2]},
        "name",
    )
    if existing:
        return existing

    process = frappe.get_doc("Procurement Process", award.procurement_process)
    if process.status not in ("Award Approved", "Closed"):
        frappe.throw(_("The procurement award must be approved."))

    doc = frappe.get_doc(
        {
            "doctype": "Procurement Contract",
            "award_decision": award.name,
            "procurement_process": process.name,
            "supplier": award.awarded_supplier,
            "contract_value": award.awarded_amount,
            "company": process.company,
            "project": process.project,
            "currency": process.currency,
            "contract_title": process.title,
        }
    )
    doc.insert()
    return doc.name


@frappe.whitelist()
def create_or_open_contract_record(contract_name, target_doctype):
    allowed = {
        "Commitment Ledger": "procurement_process",
        "Procure Acceptance": "procurement_process",
        "Procurement Amendment": "procurement_process",
    }
    if target_doctype not in allowed:
        frappe.throw(_("Unsupported contract action."))

    contract = frappe.get_doc("Procurement Contract", contract_name)
    contract.check_permission("read")

    if not frappe.has_permission(target_doctype, "create"):
        frappe.throw(
            _("Not permitted to create {0}.").format(target_doctype),
            frappe.PermissionError,
        )

    if contract.status not in ("Active", "Under Approval"):
        frappe.throw(_("The contract must be active or under approval."))

    filters = {
        allowed[target_doctype]: contract.procurement_process,
        "docstatus": ["<", 2],
    }
    if target_doctype == "Commitment Ledger":
        existing = frappe.db.get_value(target_doctype, filters, "name")
        if existing:
            return existing

    values = {
        "doctype": target_doctype,
        "procurement_process": contract.procurement_process,
    }
    meta = frappe.get_meta(target_doctype)
    for field, value in (
        ("company", contract.company),
        ("project", contract.project),
        ("budget_line", contract.budget_line),
        ("currency", contract.currency),
    ):
        if meta.has_field(field):
            values[field] = value

    doc = frappe.get_doc(values)
    doc.insert()
    return doc.name
