from __future__ import annotations

import frappe

ROLES = (
    "Accountability Manager", "Accountability Officer", "Compliance Manager",
    "Internal Auditor", "Investigator", "Safeguarding Focal Point", "PSEA Focal Point",
)

CASE_TYPES = (
    ("Complaint", "Complaint", 1, 1, 1, 0, "Standard", 2, 2, 15, 7),
    ("Feedback", "Feedback", 1, 1, 0, 0, "Standard", 2, 2, 15, 7),
    ("Suggestion", "Suggestion", 1, 1, 0, 0, "Standard", 2, 2, 15, 7),
    ("Information Request", "Information Request", 1, 1, 0, 0, "Standard", 2, 2, 10, 7),
    ("Assistance Request", "Assistance Request", 1, 1, 1, 0, "Standard", 2, 2, 15, 7),
    ("Grievance", "Grievance", 0, 1, 1, 0, "Restricted", 2, 2, 15, 7),
    ("Appeal", "Appeal", 0, 1, 0, 0, "Restricted", 2, 2, 15, 7),
    ("Whistleblowing Report", "Whistleblowing Report", 1, 1, 1, 1, "Highly Confidential", 1, 1, 30, 7),
    ("Positive Feedback", "Positive Feedback", 1, 0, 0, 0, "Standard", 2, 2, 15, 7),
)

CATEGORIES = (
    ("Human Resources", "Human Resources", 0, "Medium", "Restricted", "HR Manager", "Human Resources"),
    ("Aid Assistance", "Aid Assistance", 0, "Medium", "Standard", "Accountability Officer", "MEAL / Accountability"),
    ("Beneficiary Selection", "Beneficiary Selection", 0, "High", "Restricted", "Accountability Officer", "MEAL / Accountability"),
    ("Project Delivery", "Project Delivery", 0, "Medium", "Standard", "Projects Manager", "Project Management"),
    ("Staff Conduct", "Staff Conduct", 1, "High", "Confidential", "HR Manager", "Human Resources"),
    ("Procurement", "Procurement", 0, "Medium", "Restricted", "Procurement Manager", "Procurement Review"),
    ("Supplier Performance", "Supplier Performance", 0, "Medium", "Restricted", "Procurement Manager", "Procurement Review"),
    ("Finance", "Finance", 0, "High", "Restricted", "Accounts Manager", "Compliance"),
    ("Fraud and Corruption", "Fraud and Corruption", 1, "Critical", "Highly Confidential", "Compliance Manager", "Internal Audit"),
    ("Safeguarding", "Safeguarding", 1, "Critical", "Highly Confidential", "Safeguarding Focal Point", "Safeguarding"),
    ("PSEA", "PSEA", 1, "Critical", "Highly Confidential", "PSEA Focal Point", "PSEA"),
    ("Data Protection", "Data Protection", 1, "High", "Confidential", "Compliance Manager", "Data Protection"),
    ("Conflict of Interest", "Conflict of Interest", 1, "High", "Confidential", "Compliance Manager", "Compliance"),
    ("Workplace Safety", "Workplace Safety", 0, "High", "Restricted", "HR Manager", "Human Resources"),
    ("Service Quality", "Service Quality", 0, "Medium", "Standard", "Accountability Officer", "MEAL / Accountability"),
    ("Other", "Other", 0, "Medium", "Standard", "Accountability Officer", "MEAL / Accountability"),
)

CHANNELS = (
    "Hotline", "Call Center", "SMS", "WhatsApp", "Email", "Website", "Help Desk",
    "Community Meeting", "Suggestion Box", "Field Visit", "Partner Referral", "Staff Referral",
    "In Person", "Letter", "Other",
)


def _ensure_role(name):
    if not frappe.db.exists("Role", name):
        frappe.get_doc({"doctype": "Role", "role_name": name, "desk_access": 1}).insert(ignore_permissions=True)


def _upsert(doctype, name, values):
    if frappe.db.exists(doctype, name):
        current = frappe.get_doc(doctype, name)
        changed = False
        for key, value in values.items():
            if current.get(key) in (None, "") and value not in (None, ""):
                current.set(key, value); changed = True
        if changed:
            current.save(ignore_permissions=True)
        return "adopted"
    frappe.get_doc({"doctype": doctype, **values}).insert(ignore_permissions=True)
    return "created"


def provision_governance_accountability():
    if not frappe.db.exists("DocType", "Accountability Case"):
        return {"ok": False, "skipped": "Accountability DocTypes are not installed yet"}
    for role in ROLES:
        _ensure_role(role)
    result = {"ok": True, "roles": len(ROLES), "created": [], "adopted": []}
    settings = frappe.get_single("Accountability Settings")
    defaults = {
        "default_acknowledgement_days": 2, "default_triage_days": 2,
        "default_response_days": 15, "complex_response_days": 30,
        "update_frequency_days": 7, "allow_anonymous_cases": 1,
        "force_private_attachments": 1, "hide_sensitive_details_in_notifications": 1,
        "default_accountability_role": "Accountability Officer",
        "default_accountability_manager_role": "Accountability Manager",
    }
    dirty = False
    for key, value in defaults.items():
        if settings.get(key) in (None, ""):
            settings.set(key, value); dirty = True
    if dirty:
        settings.save(ignore_permissions=True)

    for name, nature, anonymous, response, appeal, investigation, confidentiality, ack, triage, days, updates in CASE_TYPES:
        values = {
            "type_name": name, "enabled": 1, "case_nature": nature,
            "allow_anonymous": anonymous, "requires_response": response,
            "allow_appeal": appeal, "investigation_default": investigation,
            "default_confidentiality": confidentiality, "closure_approval_required": 1,
            "acknowledgement_days": ack, "triage_days": triage,
            "response_days": days, "update_frequency_days": updates,
        }
        result[_upsert("Accountability Case Type", name, values)].append(f"Case Type:{name}")

    for name, domain, sensitive, priority, confidentiality, role, referral in CATEGORIES:
        values = {
            "category_name": name, "enabled": 1, "domain": domain,
            "sensitive_category": sensitive, "default_priority": priority,
            "default_confidentiality": confidentiality,
            "default_receiving_role": role if frappe.db.exists("Role", role) else "Accountability Officer",
            "requires_investigation": int(sensitive and name in {"Fraud and Corruption", "Safeguarding", "PSEA"}),
            "specialized_referral": referral,
        }
        result[_upsert("Accountability Category", name, values)].append(f"Category:{name}")

    for name in CHANNELS:
        values = {
            "channel_name": name, "channel_kind": name, "enabled": 1,
            "allows_anonymous": int(name not in {"Email", "Staff Referral", "Partner Referral"}),
            "requires_contact": int(name in {"Email", "SMS", "WhatsApp", "Hotline", "Call Center"}),
        }
        result[_upsert("Accountability Channel", name, values)].append(f"Channel:{name}")

    _ensure_default_rules(result)
    _provision_email_templates(result)
    _provision_workspace_metrics(result)
    frappe.clear_cache()
    return result


def _ensure_default_rules(result):
    defaults = (
        (10, "PSEA", "PSEA Focal Point", "Highly Confidential", 1, "PSEA"),
        (10, "Safeguarding", "Safeguarding Focal Point", "Highly Confidential", 1, "Safeguarding"),
        (10, "Fraud and Corruption", "Compliance Manager", "Highly Confidential", 1, "Internal Audit"),
        (20, "Human Resources", "HR Manager", "Restricted", 0, "Human Resources"),
        (20, "Procurement", "Procurement Manager", "Restricted", 0, "Procurement Review"),
        (20, "Supplier Performance", "Procurement Manager", "Restricted", 0, "Procurement Review"),
        (100, "Aid Assistance", "Accountability Officer", "Standard", 0, "MEAL / Accountability"),
        (100, "Project Delivery", "Projects Manager", "Standard", 0, "Project Management"),
        (500, "Other", "Accountability Officer", "Standard", 0, "MEAL / Accountability"),
    )
    for priority, category, role, confidentiality, investigate, referral in defaults:
        actual_role = role if frappe.db.exists("Role", role) else "Accountability Officer"
        name = f"Default - {category}"
        values = {
            "rule_name": name, "enabled": 1, "priority": priority,
            "category": category, "receiving_role": actual_role,
            "confidentiality": confidentiality, "investigation_required": investigate,
            "specialized_referral": referral,
        }
        result[_upsert("Accountability Routing Rule", name, values)].append(f"Routing Rule:{name}")


def _provision_email_templates(result):
    import json
    from pathlib import Path
    path=Path(__file__).parent / "data" / "email_templates" / "accountability_templates.json"
    for data in json.loads(path.read_text(encoding="utf-8")):
        name=data["name"]
        if frappe.db.exists("Email Template",name):
            result["adopted"].append(f"Email Template:{name}")
        else:
            frappe.get_doc(data).insert(ignore_permissions=True)
            result["created"].append(f"Email Template:{name}")

def _provision_workspace_metrics(result):
    cards=(
        ("Open Accountability Cases","Accountability Case",[["Accountability Case","status","not in",["Closed","Withdrawn","Duplicate","Out of Scope"]]],"Blue"),
        ("Overdue Accountability Cases","Accountability Case",[["Accountability Case","overdue","=",1]],"Red"),
        ("Critical Enterprise Risks","Enterprise Risk",[["Enterprise Risk","priority","=","Critical"],["Enterprise Risk","status","!=","Closed"]],"Red"),
        ("Noncompliant Obligations","Compliance Obligation",[["Compliance Obligation","current_compliance_status","=","Noncompliant"]],"Orange"),
        ("Overdue Corrective Actions","Corrective Action",[["Corrective Action","due_date","<","Today"],["Corrective Action","status","not in",["Closed","Cancelled"]]],"Yellow"),
    )
    for name,dt,filters,color in cards:
        if frappe.db.exists("Number Card",name):result["adopted"].append(f"Number Card:{name}");continue
        frappe.get_doc({"doctype":"Number Card","name":name,"label":name,"type":"Document Type","document_type":dt,"function":"Count","is_standard":0,"is_public":1,"module":"QOrg","filters_json":frappe.as_json(filters),"color":color,"show_percentage_stats":0}).insert(ignore_permissions=True)
        result["created"].append(f"Number Card:{name}")
