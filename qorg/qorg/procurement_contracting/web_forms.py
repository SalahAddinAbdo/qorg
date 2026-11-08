from __future__ import annotations

import frappe

from qorg.qorg.people_and_opportunities.web_form_policy import apply_managed_web_form_settings


def section(label):
    return {"fieldtype": "Section Break", "label": label}


def column():
    return {"fieldtype": "Column Break"}


def page(label):
    return {"fieldtype": "Page Break", "label": label}


def field(fieldname, required=False, read_only=False, label=None):
    return {"fieldname": fieldname, "required": required, "read_only": read_only, "label": label}


WEB_FORMS = [
    {
        "title": "Supplier Registration",
        "route": "supplier-registration",
        "doc_type": "Supplier Registration",
        "login_required": 1,
        "anonymous": 0,
        "allow_multiple": 0,
        "allow_edit": 1,
        "allow_delete": 0,
        "show_list": 0,
        "allow_print": 1,
        "apply_document_permissions": 1,
        "show_attachments": 1,
        "key_required": 0,
        "introduction_text": "Complete all mandatory legal, contact, capability, document and compliance information. Fields marked with an asterisk are required.",
        "success_message": "Your supplier profile has been saved successfully.",
        "submit_button_label": "Save Supplier Profile",
        "layout": [
            page("Organization"),
            section("Legal Identity"), field("legal_name", True), field("trade_name"), column(), field("supplier_type", True), field("country", True),
            section("Registration Details"), field("registration_number", True), field("tax_id", True), column(), field("year_established"), field("employee_count"),
            page("Contact and Address"),
            section("Registered Address"), field("address_line_1", True), field("address_line_2"), field("city", True), column(), field("phone", True), field("email", True), field("website"),
            section("Primary Contact"), field("contact_person", True), field("contact_designation", True), column(), field("contact_phone", True), field("contact_email", True),
            page("Capabilities"),
            section("Business Capability"), field("business_sectors", True), field("geographic_coverage", True),
            section("Experience and Past Performance"), field("experience_summary", True),
            page("Documents"),
            section("Mandatory Documents"), field("registration_certificate", True), field("tax_certificate", True), column(), field("company_profile", True), field("bank_confirmation"),
            section("Supporting Documents"), field("licenses_certificates"), field("references_document"), column(), field("documents"),
            page("Compliance"),
            section("Supplier Declarations"), field("conflict_of_interest", True), field("sanctions_declaration", True), column(), field("anti_fraud_declaration", True), field("data_consent", True),
            section("Additional Declaration"), field("declarations"),
            page("Bank Information"),
            section("Settlement Account"), field("bank_name"), field("account_name"), field("account_number"), column(), field("iban"), field("swift_code"), field("bank_currency"),
            page("Review"),
            section("Profile Review Status"), field("registration_status", read_only=True), field("profile_locked", read_only=True), column(), field("risk_rating", read_only=True), field("review_expiry_date", read_only=True),
        ],
    },
    {
        "title": "Tender Submission",
        "route": "tender-submission",
        "doc_type": "Procurement Submission",
        "login_required": 1,
        "anonymous": 0,
        "allow_multiple": 1,
        "allow_edit": 1,
        "allow_delete": 0,
        "show_list": 1,
        "allow_print": 1,
        "apply_document_permissions": 1,
        "show_attachments": 1,
        "key_required": 0,
        "introduction_text": "Submit the required technical and financial documents before the deadline. Fields marked with an asterisk are required.",
        "success_message": "Your tender submission has been saved successfully.",
        "submit_button_label": "Save Tender Submission",
        "layout": [
            page("Opportunity"), section("Procurement Opportunity"), field("procurement_process", True), field("procurement_notice", True), column(), field("supplier_registration", True), field("supplier", read_only=True),
            page("Technical Offer"), section("Technical Proposal"), field("technical_proposal", True), field("bid_security"),
            page("Financial Offer"), section("Financial Proposal"), field("financial_proposal", True),
            page("Confirmation"), section("Supplier Profile Confirmation"), field("profile_current_confirmation", True), field("profile_confirmation_on", read_only=True), section("Declaration"), field("declaration", True),
            page("Submission Status"), section("Status and Version"), field("submission_status", read_only=True), field("submission_version", read_only=True), column(), field("submitted_at", read_only=True), field("supersedes_submission", read_only=True), section("Withdrawal"), field("withdrawn_on", read_only=True), field("withdrawal_reason", read_only=True),
        ],
    },
]


def _set(row, meta, fieldname, value):
    if meta.has_field(fieldname):
        row.set(fieldname, value)


def _apply_settings(doc, definition):
    apply_managed_web_form_settings(doc, {
        **definition,
        "published": 1,
        "is_standard": 0,
        "custom_css": "",
        "client_script": "",
        "design": {
            "qorg_web_form_design_mode": "Use Global Setting",
            "qorg_web_form_header_style_override": "Use Global Setting",
            "qorg_web_form_max_content_width_override": None,
            "qorg_web_form_privacy_notice_mode": "Use Global Setting",
            "qorg_web_form_sticky_actions_mode": "Use Global Setting",
            "qorg_web_form_child_name_mode": "Use Global Setting",
            "qorg_apply_managed_web_form_design": 1,
            "qorg_managed_css_version": "4.2.0",
            "qorg_managed_css_update_available": 0,
        },
    })


def _rebuild_fields(doc, definition):
    table_field = next(
        (f.fieldname for f in doc.meta.fields if f.fieldtype == "Table" and f.options == "Web Form Field"),
        None,
    )
    if not table_field:
        frappe.throw("Web Form Field table was not found.")

    child_meta = frappe.get_meta(doc.meta.get_field(table_field).options)
    target_meta = frappe.get_meta(definition["doc_type"])
    doc.set(table_field, [])
    layout_index = 0

    for item in definition["layout"]:
        row = doc.append(table_field, {})
        fieldtype = item.get("fieldtype")
        if fieldtype in {"Page Break", "Section Break", "Column Break"}:
            layout_index += 1
            if fieldtype != "Page Break":
                _set(row, child_meta, "fieldname", f"qorg_layout_{layout_index}")
            _set(row, child_meta, "fieldtype", fieldtype)
            _set(row, child_meta, "label", item.get("label") or "")
            continue

        target = target_meta.get_field(item["fieldname"])
        if not target:
            frappe.throw(f"Missing field {definition['doc_type']}.{item['fieldname']}")
        _set(row, child_meta, "fieldname", target.fieldname)
        _set(row, child_meta, "fieldtype", target.fieldtype)
        _set(row, child_meta, "label", item.get("label") or target.label)
        _set(row, child_meta, "options", target.options)
        _set(row, child_meta, "description", target.description)
        # Frappe Web Form Field uses reqd. Keep req compatibility only when present.
        required = int(bool(item.get("required") or target.reqd))
        _set(row, child_meta, "reqd", required)
        _set(row, child_meta, "req", required)
        _set(row, child_meta, "read_only", int(bool(item.get("read_only") or target.read_only)))
        if target.fieldtype == "Link":
            _set(row, child_meta, "allow_read_on_all_link_options", 1)


def provision_procurement_web_forms():
    if not frappe.db.exists("DocType", "Web Form"):
        return
    for definition in WEB_FORMS:
        name = frappe.db.get_value("Web Form", {"route": definition["route"]}, "name")
        doc = frappe.get_doc("Web Form", name) if name else frappe.new_doc("Web Form")
        _apply_settings(doc, definition)
        _rebuild_fields(doc, definition)
        doc.save(ignore_permissions=True) if name else doc.insert(ignore_permissions=True)
    frappe.clear_cache(doctype="Web Form")
