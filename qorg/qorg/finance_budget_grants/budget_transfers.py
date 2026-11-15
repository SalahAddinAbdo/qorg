from __future__ import annotations
import frappe
from frappe import _
from frappe.utils import flt, now_datetime
from .actuals import get_posted_actual
from .commitments import get_open_commitments

APPROVED_DONOR_STATUSES = ("Approved", "Approved with Conditions")

def _is_transfer(doc):
    return bool(doc.get("budget_transfer_required") or doc.get("change_type") == "Budget Change")

def _rows(doc):
    return doc.get("budget_transfer_rows") or []

def _amount(line):
    return flt(line.get("line_cost") or line.get("current_approved_amount"))

def _ctx(name, lock=False):
    if lock:
        frappe.db.sql("select name from `tabBudget Line` where name=%s for update", name)
    doc = frappe.get_doc("Budget Line", name)
    return doc, _amount(doc)

def _transferred_out(line):
    return flt(frappe.db.sql("""
        select coalesce(sum(r.transfer_amount), 0)
        from `tabBudget Transfer Audit Row` r
        inner join `tabBudget Transfer Audit` a on a.name=r.parent
        where r.source_budget_line=%s and ifnull(a.reversed_on, '')=''
    """, line)[0][0])

def validate_budget_transfer(doc, method=None):
    if not _is_transfer(doc):
        return
    rows = _rows(doc)
    if not rows:
        frappe.throw(_("Budget Transfer Rows are required."))
    seen = set()
    total = 0
    donor_required = False
    for row in rows:
        if not row.source_budget_line or not row.target_budget_line or row.source_budget_line == row.target_budget_line:
            frappe.throw(_("Source and target Budget Lines must be different."))
        key = (row.source_budget_line, row.target_budget_line)
        if key in seen:
            frappe.throw(_("Duplicate budget transfer pair."))
        seen.add(key)
        amount = flt(row.transfer_amount)
        if amount <= 0:
            frappe.throw(_("Transfer Amount must be greater than zero."))
        source, source_amount = _ctx(row.source_budget_line)
        target, target_amount = _ctx(row.target_budget_line)
        if source.project != doc.project or target.project != doc.project:
            frappe.throw(_("Both Budget Lines must belong to the Project Change Request project."))
        for field in ("project", "company", "funding_agreement", "source_donor"):
            if source.meta.has_field(field) and target.meta.has_field(field) and source.get(field) != target.get(field):
                frappe.throw(_("Budget transfer requires the same {0}.").format(field.replace("_", " ").title()))
        currency = source.get("currency") or target.get("currency") or doc.get("project_currency")
        if source.get("currency") and target.get("currency") and source.currency != target.currency:
            frappe.throw(_("Cross-currency budget transfers are not allowed."))
        actual = get_posted_actual(project=source.project, budget_line=source.name)
        commitment = get_open_commitments(project=source.project, budget_line=source.name, company=source.get("company"), currency=currency).get("open_commitment", 0)
        available = source_amount - actual - commitment
        if amount > available:
            frappe.throw(_("Transfer exceeds available balance for {0}. Available: {1}").format(source.name, available))
        original = flt(source.get("original_approved_amount") or source_amount)
        cumulative = _transferred_out(source.name) + amount
        percent = 100 * cumulative / original if original else 100
        limit = flt(source.get("flexibility_percent") or 10)
        row.currency = currency
        row.source_previous_amount = source_amount
        row.source_new_amount = source_amount - amount
        row.target_previous_amount = target_amount
        row.target_new_amount = target_amount + amount
        row.flexibility_percent = limit
        row.transfer_percent = percent
        row.exceeds_flexibility = percent > limit
        donor_required = donor_required or bool(row.exceeds_flexibility)
        total += amount
    doc.budget_transfer_amount = total
    doc.donor_approval_required = int(donor_required)
    if donor_required and doc.get("donor_approval_status") not in APPROVED_DONOR_STATUSES:
        doc.change_applied = 0

def apply_approved_budget_transfer(doc, method=None):
    if not _is_transfer(doc) or doc.docstatus != 1 or doc.get("implementation_status") != "Implemented" or doc.get("change_applied"):
        return
    if doc.get("donor_approval_required") and doc.get("donor_approval_status") not in APPROVED_DONOR_STATUSES:
        frappe.throw(_("Approved donor authorization is required."))
    if frappe.db.exists("Budget Transfer Audit", {"project_change_request": doc.name}):
        frappe.throw(_("This Project Change Request already has a Budget Transfer Audit."))
    rows = []
    for item in _rows(doc):
        source, source_before = _ctx(item.source_budget_line, True)
        target, target_before = _ctx(item.target_budget_line, True)
        amount = flt(item.transfer_amount)
        actual = get_posted_actual(project=source.project, budget_line=source.name)
        commitment = get_open_commitments(project=source.project, budget_line=source.name, company=source.get("company"), currency=item.currency).get("open_commitment", 0)
        if amount > source_before - actual - commitment:
            frappe.throw(_("Available balance changed for {0}; review the transfer again.").format(source.name))
        source.db_set("line_cost", source_before - amount, update_modified=False)
        target.db_set("line_cost", target_before + amount, update_modified=False)
        rows.append({
            "source_budget_line": source.name, "target_budget_line": target.name,
            "transfer_amount": amount, "currency": item.currency,
            "source_previous_amount": source_before, "source_new_amount": source_before - amount,
            "target_previous_amount": target_before, "target_new_amount": target_before + amount,
            "flexibility_percent": item.flexibility_percent, "transfer_percent": item.transfer_percent,
            "exceeded_flexibility": item.exceeds_flexibility,
        })
    audit = frappe.get_doc({
        "doctype": "Budget Transfer Audit", "project_change_request": doc.name,
        "project": doc.project, "funding_agreement": doc.get("funding_agreement"),
        "applied_on": now_datetime(), "applied_by": frappe.session.user,
        "total_transferred": sum(flt(x["transfer_amount"]) for x in rows),
        "currency": rows[0].get("currency") if rows else None,
        "donor_approval_required": doc.get("donor_approval_required"),
        "donor_approval_status": doc.get("donor_approval_status"),
        "donor_reference": doc.get("donor_approval_reference") or doc.get("donor_reference"),
        "rows": rows,
    }).insert(ignore_permissions=True)
    doc.db_set("change_applied", 1, update_modified=False)
    doc.db_set("budget_transfer_applied_on", audit.applied_on, update_modified=False)
    doc.db_set("budget_transfer_applied_by", frappe.session.user, update_modified=False)
    doc.db_set("budget_transfer_audit", audit.name, update_modified=False)

def reverse_budget_transfer(doc, method=None):
    if not doc.get("change_applied") or not doc.get("budget_transfer_audit"):
        return
    audit = frappe.get_doc("Budget Transfer Audit", doc.budget_transfer_audit)
    if audit.get("reversed_on"):
        return
    for row in audit.rows:
        source, source_now = _ctx(row.source_budget_line, True)
        target, target_now = _ctx(row.target_budget_line, True)
        amount = flt(row.transfer_amount)
        if target_now < amount:
            frappe.throw(_("Cannot reverse transfer because target Budget Line balance is insufficient."))
        source.db_set("line_cost", source_now + amount, update_modified=False)
        target.db_set("line_cost", target_now - amount, update_modified=False)
    audit.db_set("reversed_on", now_datetime(), update_modified=False)
    audit.db_set("reversed_by", frappe.session.user, update_modified=False)

def sync_funding_agreement_to_project(doc, method=None):
    if not doc.get("project") or not doc.get("donor"):
        return
    rows = frappe.get_all("Project Funding Source", filters={
        "parent": doc.project, "parenttype": "Project", "parentfield": "custom_funding_sources", "donor": doc.donor,
    }, pluck="name")
    if len(rows) == 1:
        frappe.db.set_value("Project Funding Source", rows[0], {
            "funding_agreement": doc.name,
            "agreement_reference": doc.agreement_reference,
            "donor_currency": doc.agreement_currency,
            "approved_amount_donor_currency": doc.agreement_amount,
            "exchange_rate": doc.exchange_rate,
            "funding_start_date": doc.start_date,
            "funding_end_date": doc.end_date,
            "eligibility_start_date": doc.eligibility_start_date,
            "eligibility_end_date": doc.eligibility_end_date,
            "flexibility_percent": doc.flexibility_percent,
        }, update_modified=False)
