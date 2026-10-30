from __future__ import annotations

import frappe

PRESET_DOCTYPE = "Q Org Design Preset"  # Existing technical identifier.
SETTINGS_DOCTYPE = "Q Org Design System Settings"  # Existing technical identifier.
PRESET_RENAMES = {
    "Q Org Comfortable": "QOrg Comfortable",
    "Q Org Compact": "QOrg Compact",
}
VALUE_RENAMES = {
    "experience_style": {
        "Q Org Executive": "QOrg Executive",
        "Q Org Midnight": "QOrg Midnight",
        "Q Org Operations": "QOrg Operations",
    },
    "login_layout": {
        "Q Org Split": "QOrg Split",
        "Q Org Centered": "QOrg Centered",
        "Q Org Visual": "QOrg Visual",
    },
    "login_visual_gradient": {
        "Q Org Blue": "QOrg Blue",
        "Q Org Violet": "QOrg Violet",
        "Q Org Sunrise": "QOrg Sunrise",
    },
    "typography_policy": {"Q Org Bundled": "QOrg Bundled"},
}


def execute() -> None:
    if not frappe.db.exists("DocType", PRESET_DOCTYPE):
        return

    # Normalize legacy values before touching linked presets.
    _normalize_settings()
    _normalize_presets()
    _adopt_canonical_presets()
    frappe.clear_cache(doctype=PRESET_DOCTYPE)
    if frappe.db.exists("DocType", SETTINGS_DOCTYPE):
        frappe.clear_cache(doctype=SETTINGS_DOCTYPE)


def _adopt_canonical_presets() -> None:
    """Create canonical managed presets without framework-level rename.

    The installed Frappe build generates an invalid ``IN ()`` query when
    ``rename_doc`` is called for this DocType because it has no eligible link
    fields for User Settings. Keeping the legacy source disabled also protects
    any site-specific references outside the managed Settings Link.
    """
    for old_name, new_name in PRESET_RENAMES.items():
        old_exists = bool(frappe.db.exists(PRESET_DOCTYPE, old_name))
        new_exists = bool(frappe.db.exists(PRESET_DOCTYPE, new_name))

        if old_exists and not new_exists:
            source = frappe.get_doc(PRESET_DOCTYPE, old_name)
            target = frappe.copy_doc(source)
            target.name = None
            target.preset_name = new_name
            target.flags.ignore_permissions = True
            target.insert(ignore_permissions=True)
            new_exists = True

        if not old_exists:
            continue

        if new_exists:
            _replace_active_preset(old_name, new_name)

        # Retain the legacy record for unknown external links, but prevent it
        # from appearing as an active managed choice. No destructive delete.
        frappe.db.set_value(
            PRESET_DOCTYPE,
            old_name,
            {
                "enabled": 0,
                "description": "Obsolete managed preset retained for link safety.",
            },
            update_modified=False,
        )

def _replace_active_preset(old_name: str, new_name: str) -> None:
    if not frappe.db.exists("DocType", SETTINGS_DOCTYPE):
        return
    if frappe.db.get_single_value(SETTINGS_DOCTYPE, "active_preset") == old_name:
        frappe.db.set_single_value(SETTINGS_DOCTYPE, "active_preset", new_name)


def _normalize_settings() -> None:
    if not frappe.db.exists("DocType", SETTINGS_DOCTYPE):
        return

    settings = frappe.get_single(SETTINGS_DOCTYPE)
    changed = _apply_value_map(settings)
    if settings.active_preset in PRESET_RENAMES:
        target = PRESET_RENAMES[settings.active_preset]
        if frappe.db.exists(PRESET_DOCTYPE, target):
            settings.active_preset = target
            changed = True
    if changed:
        settings.flags.ignore_permissions = True
        settings.save()


def _normalize_presets() -> None:
    for name in frappe.get_all(PRESET_DOCTYPE, pluck="name"):
        doc = frappe.get_doc(PRESET_DOCTYPE, name)
        if _apply_value_map(doc):
            doc.flags.ignore_permissions = True
            doc.save()


def _apply_value_map(doc) -> bool:
    changed = False
    for fieldname, mapping in VALUE_RENAMES.items():
        if not doc.meta.has_field(fieldname):
            continue
        current = doc.get(fieldname)
        if current in mapping:
            doc.set(fieldname, mapping[current])
            changed = True
    return changed
