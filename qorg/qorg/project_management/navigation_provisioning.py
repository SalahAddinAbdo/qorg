from __future__ import annotations

import json

import frappe

from qorg.qorg.project_management.workspace_integrations import (
    MANAGED_CARD_PREFIX,
    STANDARD_WORKSPACE_INTEGRATIONS,
)

APP_MODULE = "QOrg"
SIDEBAR = "Q Org"
DESKTOP_ICON = "Q Org"

STANDARD_QORG_WORKSPACES = (
    "Q Management Hub",
    "People & Recruitment",
    "Projects & Tasks",
    "Workflow & Documents",
    "Master Data",
    "Reports & Analytics",
)

NAVIGATION_PROVIDERS = (
    "qorg.qorg.people_and_opportunities.navigation.WORKSPACE_CONTRIBUTIONS",
    "qorg.qorg.recruitment_extensions.navigation.WORKSPACE_CONTRIBUTIONS",
    "qorg.qorg.project_management.navigation.WORKSPACE_CONTRIBUTIONS",
)

LEGACY_SIDEBAR_DEFINITIONS = [
    ("Q Management Hub", "Workspace", "Q Management Hub", "home"),
    ("People & Recruitment", "Workspace", "People & Recruitment", "users"),
    ("Projects & Tasks", "Workspace", "Projects & Tasks", "folder-normal"),
    ("Workflow & Documents", "Workspace", "Workflow & Documents", "workflow"),
    ("Master Data", "Workspace", "Master Data", "folder-normal"),
    ("Reports & Analytics", "Workspace", "Reports & Analytics", "chart"),
]


def _get_workspace_groups():
    """Merge package-owned navigation contributions without duplicating cards or links."""
    merged = {name: [] for name in STANDARD_QORG_WORKSPACES}

    for provider_path in NAVIGATION_PROVIDERS:
        try:
            contributions = frappe.get_attr(provider_path) or {}
        except Exception:
            frappe.log_error(
                title="QOrg Navigation Provider Error",
                message=frappe.get_traceback(),
            )
            continue

        for workspace_name, groups in contributions.items():
            merged.setdefault(workspace_name, [])
            merged[workspace_name].extend(groups or [])

    normalized = {}
    for workspace_name, groups in merged.items():
        card_order = []
        card_map = {}

        for label, link_type, items in groups:
            key = (label, link_type)
            if key not in card_map:
                card_order.append(key)
                card_map[key] = []

            for item in items or ():
                if item not in card_map[key]:
                    card_map[key].append(item)

        normalized[workspace_name] = [
            (label, link_type, card_map[(label, link_type)])
            for label, link_type in card_order
        ]

    return normalized


def _audit_standard_workspace_shells():
    missing = [name for name in STANDARD_QORG_WORKSPACES if not _exists("Workspace", name)]
    if missing:
        frappe.log_error(
            title="Missing QOrg Standard Workspaces",
            message=(
                "The following standard QOrg workspace shells were not synchronized "
                "from app files: " + "; ".join(missing)
            ),
        )
    return missing


def _exists(doctype, name):
    return bool(frappe.db.exists(doctype, name))


def _report_is_query(name):
    report_type = frappe.db.get_value("Report", name, "report_type") or ""
    return 1 if report_type in ("Script Report", "Query Report") else 0


def _valid_items(link_type, items):
    return [item for item in items if _exists(link_type, item)]


def _shortcut(name, link_type, color="Blue"):
    row = {
        "label": name, "link_to": name, "type": link_type, "color": color,
        "doc_view": "List", "stats_filter": "[]",
    }
    if link_type == "Report":
        row["is_query_report"] = _report_is_query(name)
    return row


def _workspace_link_rows(groups):
    rows = []
    for label, link_type, items in groups:
        valid = _valid_items(link_type, items)
        if not valid:
            continue
        rows.append({"label": label, "type": "Card Break", "link_count": len(valid)})
        for item in valid:
            row = {
                "label": item, "type": "Link", "link_type": link_type,
                "link_to": item, "onboard": 0,
            }
            if link_type == "Report":
                row["is_query_report"] = _report_is_query(item)
            rows.append(row)
    return rows


def _content(title, shortcuts, card_labels):
    blocks = [{
        "id": "qorg_header", "type": "header",
        "data": {"text": f'<span class="h4">{title}</span>', "col": 12},
    }]
    for index, row in enumerate(shortcuts):
        blocks.append({
            "id": f"qorg_shortcut_{index}", "type": "shortcut",
            "data": {"shortcut_name": row["label"], "col": 3},
        })
    if card_labels:
        blocks.append({"id": "qorg_spacer", "type": "spacer", "data": {"col": 12}})
    for index, label in enumerate(card_labels):
        blocks.append({
            "id": f"qorg_card_{index}", "type": "card",
            "data": {"card_name": label, "col": 4},
        })
    return json.dumps(blocks, separators=(",", ":"))


def _save_workspace(name, groups):
    """Populate a standard workspace shell with dynamic, package-contributed content."""
    if not _exists("Workspace", name):
        frappe.log_error(
            title="Missing QOrg Standard Workspace",
            message=(
                f"Workspace {name} was not synchronized from the standard workspace "
                "JSON files bundled with qorg. Dynamic content was not created."
            ),
        )
        return

    supported = {"DocType", "Report", "Page", "Dashboard", "URL"}
    normalized = []
    for label, link_type, items in groups:
        if link_type not in supported:
            continue
        valid = _valid_items(link_type, items)
        if valid:
            normalized.append((label, link_type, valid))

    shortcuts = []
    for _, link_type, items in normalized:
        for item in items:
            shortcuts.append(
                _shortcut(
                    item,
                    link_type,
                    "Green" if link_type == "Report" else "Blue",
                )
            )
            if len(shortcuts) == 8:
                break
        if len(shortcuts) == 8:
            break

    doc = frappe.get_doc("Workspace", name)
    values = {
        "title": name,
        "label": name,
        "module": APP_MODULE,
        "type": "Workspace",
        "public": 1,
        "is_hidden": 0,
        "icon": "project",
        "content": _content(
            name,
            shortcuts,
            [label for label, _, _ in normalized],
        ),
        "shortcuts": shortcuts,
        "links": _workspace_link_rows(normalized),
    }

    changed = False
    for key, value in values.items():
        if doc.get(key) != value:
            doc.set(key, value)
            changed = True

    if changed:
        doc.save(ignore_permissions=True)


def _save_legacy_sidebar():
    items = []
    for label, link_type, target, icon in LEGACY_SIDEBAR_DEFINITIONS:
        if not _exists(link_type, target):
            continue
        row = {
            "label": label, "type": "Link", "link_type": link_type,
            "link_to": target, "icon": icon, "child": 0, "indent": 0,
            "collapsible": 1, "keep_closed": 0, "show_arrow": 0,
        }
        if link_type == "Report":
            row["is_query_report"] = _report_is_query(target)
        items.append(row)
    values = {
        "title": SIDEBAR, "module": APP_MODULE, "standard": 1,
        "app": "qorg", "header_icon": "project", "items": items,
    }
    if _exists("Workspace Sidebar", SIDEBAR):
        doc = frappe.get_doc("Workspace Sidebar", SIDEBAR)
        for key, value in values.items():
            doc.set(key, value)
        doc.save(ignore_permissions=True)
    else:
        frappe.get_doc({"doctype": "Workspace Sidebar", "name": SIDEBAR, **values}).insert(ignore_permissions=True)


def _save_legacy_icon():
    values = {
        "label": DESKTOP_ICON, "icon_type": "Link",
        "link_type": "Workspace Sidebar", "link_to": SIDEBAR, "sidebar": "",
        "app": "qorg", "icon": "project",
        "logo_url": "/assets/qorg/images/qorg_project_cycle.png",
        "hidden": 0, "standard": 1, "restrict_removal": 1,
        "idx": 50, "parent_icon": "",
    }
    meta = frappe.get_meta("Desktop Icon")
    if _exists("Desktop Icon", DESKTOP_ICON):
        doc = frappe.get_doc("Desktop Icon", DESKTOP_ICON)
        for key, value in values.items():
            if meta.has_field(key):
                doc.set(key, value)
        doc.save(ignore_permissions=True)
    else:
        frappe.get_doc({
            "doctype": "Desktop Icon", "name": DESKTOP_ICON,
            **{key: value for key, value in values.items() if meta.has_field(key)},
        }).insert(ignore_permissions=True)


def _resolve_workspace(candidates, keywords=()):
    for candidate in candidates:
        if _exists("Workspace", candidate):
            return candidate

    # Fallback for installations where the standard workspace has a different
    # technical name but a recognizable title/label.
    rows = frappe.get_all(
        "Workspace",
        fields=["name", "title", "label"],
        limit_page_length=0,
    )
    lowered_keywords = [str(value).lower() for value in keywords if value]
    for row in rows:
        haystack = " ".join([
            str(row.get("name") or ""),
            str(row.get("title") or ""),
            str(row.get("label") or ""),
        ]).lower()
        if any(keyword in haystack for keyword in lowered_keywords):
            return row.name
    return ""


def _remove_managed_cards(doc):
    cleaned_links = []
    skipping = False
    for row in doc.links or []:
        if row.type == "Card Break":
            skipping = (row.label or "").startswith(MANAGED_CARD_PREFIX)
            if skipping:
                continue
        elif skipping and row.type == "Link":
            continue
        else:
            skipping = False
        cleaned_links.append(row.as_dict())

    try:
        content = json.loads(doc.content or "[]")
    except Exception:
        content = []
    if not isinstance(content, list):
        content = []
    cleaned_content = []
    for block in content:
        data = block.get("data") or {}
        card_name = data.get("card_name") or ""
        block_id = block.get("id") or ""
        if card_name.startswith(MANAGED_CARD_PREFIX) or block_id.startswith("qorg_standard_"):
            continue
        cleaned_content.append(block)
    return cleaned_links, cleaned_content


def _integrate_standard_workspace(workspace_name, cards):
    doc = frappe.get_doc("Workspace", workspace_name)
    links, content = _remove_managed_cards(doc)

    for card_index, card in enumerate(cards):
        valid_items = []
        for link_type, target, label in card.get("items") or ():
            if link_type not in {"DocType", "Page", "Report"} or not _exists(link_type, target):
                continue
            valid_items.append((link_type, target, label))
        if not valid_items:
            continue

        card_label = card["label"]
        links.append({"label": card_label, "type": "Card Break", "link_count": len(valid_items)})
        for link_type, target, label in valid_items:
            row = {
                "label": label, "type": "Link", "link_type": link_type,
                "link_to": target, "onboard": 0,
            }
            if link_type == "Report":
                row["is_query_report"] = _report_is_query(target)
            links.append(row)

        if card_index == 0:
            content.append({
                "id": "qorg_standard_cards_spacer",
                "type": "spacer", "data": {"col": 12},
            })
        content.append({
            "id": f"qorg_standard_card_{card_index}",
            "type": "card", "data": {"card_name": card_label, "col": 4},
        })

    doc.set("links", links)
    doc.content = json.dumps(content, separators=(",", ":"))
    doc.save(ignore_permissions=True)


def _integrate_standard_workspaces():
    for definition in STANDARD_WORKSPACE_INTEGRATIONS:
        workspace_name = _resolve_workspace(
            definition["workspace_candidates"],
            definition.get("workspace_keywords") or (),
        )
        if workspace_name:
            _integrate_standard_workspace(workspace_name, definition["cards"])


def _provision_legacy_navigation_fallback():
    """Keep the v16 Desktop Icons fallback usable while Frappe still supports it.

    The standard app-owned Sidebar is shipped from qorg/qorg/sidebar and is the
    source of truth for the new Desk navigation. These legacy records are kept
    deliberately small and are not used to manage the new Sidebar layer.
    """
    if frappe.db.exists("DocType", "Workspace Sidebar"):
        _save_legacy_sidebar()

    if frappe.db.exists("DocType", "Desktop Icon"):
        _save_legacy_icon()


def provision_q_org_navigation():
    """Provision QOrg workspaces without overwriting the new Sidebar layer.

    Navigation providers contribute dynamic cards and links to the six stable
    QOrg workspace shells. This lets functional packages add DocTypes, reports,
    pages, and dashboards without requiring repeated edits to the app Sidebar.
    """
    _audit_standard_workspace_shells()

    for name, groups in _get_workspace_groups().items():
        _save_workspace(name, groups)

    _integrate_standard_workspaces()
    _provision_legacy_navigation_fallback()
    frappe.clear_cache()
