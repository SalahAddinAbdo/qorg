import frappe
from frappe import _

def execute(filters=None):
    filters=filters or {}
    columns=[{'label': 'Supplier', 'fieldname': 'supplier', 'fieldtype': 'Link', 'width': 180, 'options': 'Supplier'}, {'label': 'Submission', 'fieldname': 'submission', 'fieldtype': 'Link', 'width': 180, 'options': 'Procurement Submission'}, {'label': 'Technical', 'fieldname': 'technical_score', 'fieldtype': 'Float', 'width': 100}, {'label': 'Financial', 'fieldname': 'financial_score', 'fieldtype': 'Float', 'width': 100}, {'label': 'Total', 'fieldname': 'total_score', 'fieldtype': 'Float', 'width': 100}, {'label': 'Rank', 'fieldname': 'rank', 'fieldtype': 'Int', 'width': 70}, {'label': 'Recommendation', 'fieldname': 'recommendation', 'fieldtype': 'Data', 'width': 150}]
    for column in columns:
        column["label"] = _(column["label"])
    fields=[c["fieldname"] for c in columns]
    allowed_filters = set(fields)
    filters = {key: value for key, value in filters.items() if value not in (None, "", []) and key in allowed_filters}
    data=frappe.get_all("Bid Summary Row", fields=fields, filters=filters, order_by="modified desc", limit_page_length=500)
    status_field = next((f for f in ("status", "submission_status", "registration_status") if data and f in data[0]), None)
    counts = {}
    if status_field:
        for row in data: counts[row.get(status_field) or _("Not Set")] = counts.get(row.get(status_field) or _("Not Set"), 0) + 1
    chart = {"data": {"labels": list(counts), "datasets": [{"name": _("Records"), "values": list(counts.values())}]}, "type": "donut"} if counts else None
    report_summary = [{"label": _("Total Records"), "value": len(data), "indicator": "Blue", "datatype": "Int"}]
    return columns, data, None, chart, report_summary
