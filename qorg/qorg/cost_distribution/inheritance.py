"""Source-key based inheritance of Cost Distribution rows.

A distribution is inherited only from a *submitted* upstream document that
carries the same durable ``source_key``. The nearest upstream stage wins
(invoice > receipt > order > quotation > request), the current document is
never its own source, and cancelled or draft documents are ignored so that an
amendment or a cancelled order can never leak its distribution downstream.
"""
from __future__ import annotations

import frappe

REFERENCE_FIELDS = (
    ("Purchase Invoice Item", "po_detail", "Purchase Order Item"),
    ("Purchase Invoice Item", "pr_detail", "Purchase Receipt Item"),
    # Returns / debit notes keep the historical distribution of the original row.
    ("Purchase Invoice Item", "purchase_invoice_item", "Purchase Invoice Item"),
    ("Purchase Order Item", "material_request_item", "Material Request Item"),
    ("Purchase Order Item", "supplier_quotation_item", "Supplier Quotation Item"),
    ("Supplier Quotation Item", "material_request_item", "Material Request Item"),
    ("Stock Entry Detail", "material_request_item", "Material Request Item"),
)

# Nearest upstream stage first.
UPSTREAM_ORDER = {
    "Purchase Invoice": (
        "Purchase Invoice",  # original invoice for returns / debit notes
        "Purchase Receipt",
        "Purchase Order",
        "Supplier Quotation",
        "Material Request",
    ),
    "Purchase Receipt": (
        "Purchase Order",
        "Supplier Quotation",
        "Material Request",
    ),
    "Purchase Order": ("Supplier Quotation", "Material Request"),
    "Supplier Quotation": ("Material Request",),
    "Stock Entry": ("Material Request",),
}


def ensure_source_key(row):
    if not row.get("custom_distribution_source_key"):
        for child, field, source_dt in REFERENCE_FIELDS:
            if row.doctype == child and row.get(field):
                if not frappe.db.exists("DocType", source_dt):
                    continue
                if not frappe.get_meta(source_dt).has_field("custom_distribution_source_key"):
                    continue
                key = frappe.db.get_value(source_dt, row.get(field), "custom_distribution_source_key")
                if key:
                    row.custom_distribution_source_key = key
                    return key
        row.custom_distribution_source_key = frappe.generate_hash(length=20)
    return row.custom_distribution_source_key


def inherited_rows(doc, source_key):
    # Search only actual upstream stages for the current document. A global
    # newest-to-oldest list can make an earlier document inherit from a later
    # submitted document that happens to share the source key.
    for source_dt in UPSTREAM_ORDER.get(doc.doctype, ()):
        if not frappe.db.exists("DocType", source_dt):
            continue
        if not frappe.get_meta(source_dt).has_field("custom_cost_distributions"):
            continue
        parents = frappe.get_all(
            "Cost Distribution Row",
            filters={"parenttype": source_dt, "source_key": source_key},
            pluck="parent",
            limit_page_length=0,
        )
        parents = sorted({p for p in parents if not (source_dt == doc.doctype and p == doc.name)})
        if not parents:
            continue
        submitted = frappe.get_all(
            source_dt,
            filters={"name": ["in", parents], "docstatus": 1},
            fields=["name", "modified"],
            order_by="modified desc",
            limit_page_length=1,
        )
        if not submitted:
            continue
        names = frappe.get_all(
            "Cost Distribution Row",
            filters={"parenttype": source_dt, "parent": submitted[0].name, "source_key": source_key},
            pluck="name",
            order_by="idx asc",
            limit_page_length=0,
        )
        if names:
            return [frappe.get_doc("Cost Distribution Row", x) for x in names]
    return []
