from __future__ import annotations

from frappe import _


def get_data(data=None):
    """Extend ERPNext's Contract dashboard without replacing its base metadata.

    Frappe v16 calls override_doctype_dashboards hooks with ``data=...``.
    The hook must therefore accept the existing dashboard payload, mutate it
    conservatively, and return it.
    """
    data = data or {}

    non_standard = data.setdefault("non_standard_fieldnames", {})
    non_standard.update(
        {
            "Contract Amendment": "contract",
            "Purchase Order": "custom_procurement_contract",
            "Purchase Receipt": "custom_procurement_contract",
            "Purchase Invoice": "custom_procurement_contract",
            "Asset": "custom_procurement_contract",
        }
    )

    transactions = data.setdefault("transactions", [])
    _append_unique_group(
        transactions,
        _("Contract Governance"),
        ["Contract Amendment"],
    )
    _append_unique_group(
        transactions,
        _("Procurement Documents"),
        ["Purchase Order", "Purchase Receipt", "Purchase Invoice", "Asset"],
    )

    return data


def _append_unique_group(transactions, label, items):
    """Add missing dashboard links without duplicating ERPNext/QOrg groups."""
    existing_items = {
        item
        for group in transactions
        for item in (group.get("items") or [])
    }
    missing = [item for item in items if item not in existing_items]
    if missing:
        transactions.append({"label": label, "items": missing})
