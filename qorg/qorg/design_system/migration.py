from __future__ import annotations

import frappe

from qorg.qorg.design_system.provisioning import normalize_settings_values, provision_design_system
from qorg.qorg.design_system.service import SETTINGS, clear_cache


# Legacy values that can survive schema synchronization when a new field keeps
# the same fieldname but intentionally exposes a smaller option set.
LEGACY_PRESET_ALIASES = {
    "QOrg Executive Light": "Q Org Enterprise",
    "QOrg Comfortable": "Q Org Enterprise",
    "QOrg Midnight": "Q Org Dark",
    "QOrg Compact Operations": "Q Org Compact",
    "QOrg High Contrast": "Q Org Accessible",
}


def migrate_clean_theme() -> None:
    """Normalize retained v2 values before the v3 Settings document is saved.

    Frappe keeps values for columns whose fieldnames still exist after DocType
    synchronization. This is intentional and preserves data, but old Select
    values must be mapped before document validation runs.
    """
    if not frappe.db.exists("DocType", SETTINGS):
        return

    settings = frappe.get_single(SETTINGS)
    changed = normalize_settings_values(settings)

    if settings.get("active_preset") in LEGACY_PRESET_ALIASES:
        settings.active_preset = LEGACY_PRESET_ALIASES[settings.active_preset]
        changed = True

    if changed:
        settings.flags.ignore_permissions = True
        settings.save()

    provision_design_system()
    clear_cache()
