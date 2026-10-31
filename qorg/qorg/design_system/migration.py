from __future__ import annotations

import frappe

from qorg.qorg.design_system.provisioning import (
    ensure_presets,
    normalize_settings_values,
    provision_design_system,
)
from qorg.qorg.design_system.service import SETTINGS, clear_cache


def migrate_clean_theme() -> None:
    """Atomically migrate retained theme values without dangling Link errors.

    Dependency order is deliberate:
    1. Create/reconcile Q Org Design Preset Link targets.
    2. Normalize retained legacy Select and Link values.
    3. Save Settings only after every Link target exists.
    4. Run idempotent provisioning for defaults and managed reconciliation.
    """
    if not frappe.db.exists("DocType", SETTINGS):
        return

    ensure_presets()

    settings = frappe.get_single(SETTINGS)
    if normalize_settings_values(settings):
        settings.flags.ignore_permissions = True
        settings.save()

    provision_design_system()
    clear_cache()
