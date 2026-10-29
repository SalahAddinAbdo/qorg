from __future__ import annotations

import json
from pathlib import Path

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.website.utils import delete_page_cache


def provision_opportunity_portal():
    _create_custom_fields()
    _create_web_form_design_custom_fields()
    _backfill_routes()
    frappe.clear_cache(doctype="External Opportunity")
    delete_page_cache()
    return {"ok": True}


def _create_custom_fields():
    path = Path(__file__).resolve().parent / "data" / "portal_custom_fields.json"
    definitions = json.loads(path.read_text(encoding="utf-8"))
    create_custom_fields(definitions, update=True)


def _create_web_form_design_custom_fields():
    path = Path(__file__).resolve().parent / "data" / "web_form_design_custom_fields.json"
    definitions = json.loads(path.read_text(encoding="utf-8"))
    create_custom_fields(definitions, update=True)


def _backfill_routes():
    if not frappe.db.exists("DocType", "External Opportunity"):
        return

    meta = frappe.get_meta("External Opportunity")
    if not meta.has_field("route"):
        return

    from qorg.qorg.people_and_opportunities.portal import ensure_public_route

    names = frappe.get_all(
        "External Opportunity",
        filters={"publish_on_website": 1},
        pluck="name",
    )

    for name in names:
        doc = frappe.get_doc("External Opportunity", name)
        route = ensure_public_route(doc)

        if route and doc.get("route") != route:
            frappe.db.set_value(
                "External Opportunity",
                name,
                "route",
                route,
                update_modified=False,
            )
