from __future__ import annotations
from collections import defaultdict
import frappe
from frappe import _
from frappe.utils import flt


def execute(filters=None):
    filters = frappe._dict(filters or {})
    rows = _rows(filters)
    columns = _columns()
    chart = _chart(rows)
    summaries = _summaries(rows)
    return columns, rows, None, chart, summaries


def _agreement_filters(filters):
    result = {"status": ["in", ["Active", "Closing"]]}
    for field in ("company", "project", "donor"):
        if filters.get(field):
            result[field] = filters[field]
    if filters.get("funding_agreement"):
        result["name"] = filters.funding_agreement
    if filters.get("status"):
        result["status"] = filters.status
    return result


def _rows(filters):
    rows = []
    agreements = frappe.get_all("Funding Agreement", filters=_agreement_filters(filters), fields=["name", "project", "donor", "agreement_currency"])
    for agreement in agreements:
        child_filters = {"parent": agreement.name, "parenttype": "Funding Agreement"}
        if filters.get("from_date"):
            child_filters["due_date"] = [">=", filters.from_date]
        installments = frappe.get_all("Funding Installment", filters=child_filters, fields=["installment_title", "due_date", "amount", "received_amount", "status"], order_by="due_date asc")
        for installment in installments:
            if filters.get("to_date") and installment.due_date and installment.due_date > filters.to_date:
                continue
            rows.append({
                "agreement": agreement.name,
                "project": agreement.project,
                "donor": agreement.donor,
                "currency": agreement.agreement_currency,
                "outstanding": flt(installment.amount) - flt(installment.received_amount),
                **installment,
            })
    return rows


def _columns():
    return [
        {"label": _("Agreement"), "fieldname": "agreement", "fieldtype": "Link", "options": "Funding Agreement", "width": 180},
        {"label": _("Project"), "fieldname": "project", "fieldtype": "Link", "options": "Project", "width": 170},
        {"label": _("Donor"), "fieldname": "donor", "fieldtype": "Link", "options": "Donor", "width": 150},
        {"label": _("Installment"), "fieldname": "installment_title", "width": 180},
        {"label": _("Due Date"), "fieldname": "due_date", "fieldtype": "Date", "width": 105},
        {"label": _("Currency"), "fieldname": "currency", "width": 80},
        {"label": _("Planned"), "fieldname": "amount", "fieldtype": "Currency", "options": "currency", "width": 120},
        {"label": _("Received"), "fieldname": "received_amount", "fieldtype": "Currency", "options": "currency", "width": 120},
        {"label": _("Outstanding"), "fieldname": "outstanding", "fieldtype": "Currency", "options": "currency", "width": 125},
        {"label": _("Status"), "fieldname": "status", "width": 110},
    ]


def _summaries(rows):
    currencies = defaultdict(lambda: {"planned": 0, "received": 0, "outstanding": 0})
    for row in rows:
        bucket = currencies[row.currency]
        bucket["planned"] += flt(row.amount)
        bucket["received"] += flt(row.received_amount)
        bucket["outstanding"] += flt(row.outstanding)
    result = [{"value": len(rows), "label": _("Installments"), "datatype": "Int"}]
    for currency, values in sorted(currencies.items()):
        result.extend([
            {"value": values["planned"], "label": _("Planned ({0})").format(currency), "datatype": "Currency", "currency": currency},
            {"value": values["outstanding"], "label": _("Outstanding ({0})").format(currency), "datatype": "Currency", "currency": currency},
        ])
    return result


def _chart(rows):
    monthly = defaultdict(float)
    for row in rows:
        key = str(row.due_date)[:7] if row.due_date else _("No Date")
        monthly[key] += flt(row.outstanding)
    return {"data": {"labels": sorted(monthly), "datasets": [{"name": _("Outstanding"), "values": [monthly[key] for key in sorted(monthly)]}]}, "type": "line"}
