from __future__ import annotations

import json
from urllib.parse import quote

import frappe
from frappe import _
from frappe.utils import add_to_date, get_datetime, now_datetime


def _redirect(location: str):
    frappe.local.response["type"] = "redirect"
    frappe.local.response["location"] = location


def supplier_profile_path() -> str:
    name = frappe.db.get_value(
        "Supplier Registration", {"owner": frappe.session.user}, "name"
    )
    return f"/supplier-registration/{quote(name, safe='')}" if name else "/supplier-registration/new"


@frappe.whitelist()
def open_supplier_profile():
    if frappe.session.user == "Guest":
        _redirect("/login?redirect-to=/supplier-profile")
        return
    _redirect(supplier_profile_path())


def _resolve_notice(notice: str | None = None, route: str | None = None):
    value = (notice or route or frappe.form_dict.get("notice") or frappe.form_dict.get("route") or "").strip()
    if not value:
        frappe.throw(_("A procurement opportunity is required."))
    name = value if frappe.db.exists("Procurement Notice", value) else frappe.db.get_value(
        "Procurement Notice", {"route": value, "published": 1, "docstatus": 1}, "name"
    )
    if not name:
        frappe.throw(_("The selected procurement opportunity is not available."))
    return frappe.get_doc("Procurement Notice", name)


def _create_web_form_request(values: dict, reference_docname: str | None = None):
    web_form = frappe.db.get_value("Web Form", {"route": "tender-submission"}, "name")
    if not web_form:
        frappe.throw(_("Tender Submission Web Form is not configured."))
    request = frappe.new_doc("Web Form Request")
    request.web_form = web_form
    request.web_form_values = json.dumps(values or {})
    request.doc_values = json.dumps(values or {})
    if reference_docname:
        request.append("references", {
            "link_doctype": "Procurement Submission",
            "link_name": reference_docname,
        })
    if request.meta.has_field("expires_on"):
        request.expires_on = add_to_date(now_datetime(), hours=2)
    request.insert(ignore_permissions=True)
    frappe.db.commit()
    return request


def _submission_path(request, docname: str | None = None) -> str:
    key = request.get("key") or request.name
    path = f"/tender-submission/{quote(docname, safe='')}" if docname else "/tender-submission/new"
    return f"{path}?web_form_request_key={quote(key, safe='')}"


@frappe.whitelist()
def start_tender_submission(notice: str | None = None, route: str | None = None):
    if frappe.session.user == "Guest":
        target = route or notice or frappe.form_dict.get("route") or ""
        _redirect(f"/login?redirect-to={quote('/procurement-opportunity?route=' + target, safe='')}")
        return

    notice_doc = _resolve_notice(notice, route)
    if notice_doc.deadline and get_datetime(notice_doc.deadline) <= now_datetime():
        frappe.throw(_("Submissions are closed for this procurement opportunity."))

    profile = frappe.db.get_value(
        "Supplier Registration",
        {"owner": frappe.session.user},
        ["name", "supplier", "profile_locked"],
        as_dict=True,
    )
    if not profile:
        _redirect("/supplier-registration/new")
        return

    existing = frappe.db.get_value(
        "Procurement Submission",
        {
            "owner": frappe.session.user,
            "procurement_notice": notice_doc.name,
            "submission_status": ["!=", "Withdrawn"],
        },
        "name",
    )
    if existing:
        request = _create_web_form_request({}, existing)
        _redirect(_submission_path(request, existing))
        return

    values = {
        "procurement_notice": notice_doc.name,
        "procurement_process": notice_doc.procurement_process,
        "supplier_registration": profile.name,
        "supplier": profile.supplier,
        "submission_status": "Draft",
        "submission_version": 1,
    }
    request = _create_web_form_request(values)
    _redirect(_submission_path(request))


@frappe.whitelist()
def open_tender_submission(submission: str | None = None):
    """Open an existing tender through its protected standard Web Form route."""
    if frappe.session.user == "Guest":
        frappe.throw(_("Please sign in to open your bid."), frappe.PermissionError)

    submission_name = (
        submission
        or frappe.form_dict.get("submission")
        or frappe.form_dict.get("name")
        or ""
    ).strip()
    if not submission_name or not frappe.db.exists("Procurement Submission", submission_name):
        frappe.throw(_("The selected bid does not exist."))

    submission_doc = frappe.get_doc("Procurement Submission", submission_name)
    profile_names = frappe.get_all(
        "Supplier Registration", filters={"owner": frappe.session.user}, pluck="name"
    )
    permitted = submission_doc.owner == frappe.session.user or (
        submission_doc.supplier_registration
        and submission_doc.supplier_registration in profile_names
    )
    if not permitted:
        frappe.throw(_("You are not permitted to open this bid."), frappe.PermissionError)

    request = _create_web_form_request({}, submission_doc.name)
    _redirect(_submission_path(request, submission_doc.name))
