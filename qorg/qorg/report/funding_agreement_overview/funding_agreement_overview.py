from __future__ import annotations
from collections import defaultdict
import frappe
from frappe import _
from frappe.utils import flt


def execute(filters=None):
    filters = frappe._dict(filters or {})
    rows = _rows(filters)
    columns = _columns()
    summaries = _summaries(rows)
    chart = _chart(rows)
    return columns, rows, None, chart, summaries


def _rows(filters):
    db_filters = {}
    for field in ("company", "project", "donor", "status"):
        if filters.get(field):
            db_filters[field] = filters[field]
    if filters.get("funding_agreement"):
        db_filters["name"] = filters.funding_agreement
    if filters.get("from_date"):
        db_filters["end_date"] = [">=", filters.from_date]
    if filters.get("to_date"):
        db_filters["start_date"] = ["<=", filters.to_date]
    fields = [
        "name", "agreement_title", "company", "project", "donor", "status",
        "agreement_currency", "agreement_amount", "base_amount", "start_date",
        "end_date", "refundable_balance", "closeout_completed",
    ]
    return frappe.get_all("Funding Agreement", filters=db_filters, fields=fields, order_by="end_date asc, modified desc")


def _columns():
    return [
        {"label": _("Agreement"), "fieldname": "name", "fieldtype": "Link", "options": "Funding Agreement", "width": 180},
        {"label": _("Agreement Title"), "fieldname": "agreement_title", "width": 220},
        {"label": _("Project"), "fieldname": "project", "fieldtype": "Link", "options": "Project", "width": 180},
        {"label": _("Donor"), "fieldname": "donor", "fieldtype": "Link", "options": "Donor", "width": 160},
        {"label": _("Status"), "fieldname": "status", "width": 110},
        {"label": _("Currency"), "fieldname": "agreement_currency", "fieldtype": "Link", "options": "Currency", "width": 90},
        {"label": _("Agreement Amount"), "fieldname": "agreement_amount", "fieldtype": "Currency", "options": "agreement_currency", "width": 140},
        {"label": _("Base Amount"), "fieldname": "base_amount", "fieldtype": "Currency", "width": 140},
        {"label": _("Start Date"), "fieldname": "start_date", "fieldtype": "Date", "width": 105},
        {"label": _("End Date"), "fieldname": "end_date", "fieldtype": "Date", "width": 105},
        {"label": _("Refundable Balance"), "fieldname": "refundable_balance", "fieldtype": "Currency", "options": "agreement_currency", "width": 145},
        {"label": _("Closeout Completed"), "fieldname": "closeout_completed", "fieldtype": "Check", "width": 130},
    ]


def _summaries(rows):
    by_currency = defaultdict(float)
    for row in rows:
        by_currency[row.agreement_currency] += flt(row.agreement_amount)
    result = [{"value": len(rows), "label": _("Agreements"), "datatype": "Int"},
              {"value": sum(flt(row.base_amount) for row in rows), "label": _("Total Base Amount"), "datatype": "Currency"}]
    for currency, amount in sorted(by_currency.items()):
        result.append({"value": amount, "label": _("Agreement Value ({0})").format(currency), "datatype": "Currency", "currency": currency})
    return result


def _chart(rows):
    statuses = defaultdict(int)
    for row in rows:
        statuses[row.status] += 1
    return {"data": {"labels": list(statuses), "datasets": [{"name": _("Agreements"), "values": list(statuses.values())}]}, "type": "bar"}
