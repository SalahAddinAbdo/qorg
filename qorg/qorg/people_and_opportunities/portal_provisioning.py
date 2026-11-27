from __future__ import annotations

import json
from pathlib import Path

import frappe
from frappe.website.utils import delete_page_cache

from qorg.qorg.enterprise_foundation.idempotent_provisioning import (
    create_custom_fields_if_changed,
)


PORTAL_CUSTOM_FIELD_FILES = (
    "portal_custom_fields.json",
    "website_settings_custom_fields.json",
)


def provision_opportunity_portal():
    field_result = _create_custom_fields_if_changed()
    _backfill_routes()
    frappe.clear_cache(doctype="External Opportunity")
    frappe.clear_cache(doctype="Website Settings")
    delete_page_cache()
    return {
        "ok": True,
        "custom_field_files": field_result["files"],
        "custom_field_count": field_result["field_count"],
    }


def _create_custom_fields_if_changed():
    data_folder = Path(__file__).resolve().parent / "data"
    definitions = {}
    loaded_files = []
    managed_fields = set()

    for filename in PORTAL_CUSTOM_FIELD_FILES:
        path = data_folder / filename
        if not path.is_file():
            frappe.throw(f"Missing opportunity portal configuration file: {filename}")

        payload = json.loads(path.read_text(encoding="utf-8"))
        for doctype, rows in payload.items():
            target_rows = definitions.setdefault(doctype, [])
            for row in rows:
                fieldname = row.get("fieldname")
                key = (doctype, fieldname)
                if not fieldname:
                    frappe.throw(
                        f"Missing fieldname in {filename} for DocType {doctype}"
                    )
                if key in managed_fields:
                    frappe.throw(
                        f"Duplicate managed field definition: {doctype}.{fieldname}"
                    )
                managed_fields.add(key)
                target_rows.append(row)
        loaded_files.append(filename)

    create_custom_fields_if_changed(definitions, update=True)
    return {
        "files": loaded_files,
        "field_count": len(managed_fields),
    }


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
