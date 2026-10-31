from __future__ import annotations

import frappe

from qorg.qorg.design_system.provisioning import provision_baseline_records
from qorg.qorg.design_system.service import clear_legacy_theme_cache


def reset_to_frappe_baseline() -> None:
    """Reset presentation only; preserve both DocTypes and Quick Create rows."""
    provision_baseline_records()
    clear_legacy_theme_cache()
