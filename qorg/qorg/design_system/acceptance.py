from __future__ import annotations

import frappe

from qorg.qorg.design_system import BASELINE_VERSION
from qorg.qorg.design_system.service import BASELINE_PRESET, PRESET, SETTINGS, baseline_status


def audit_frappe_baseline():
    checks = []
    def add(name, passed, detail=None):
        checks.append({"name": name, "passed": bool(passed), "detail": detail})
    add("Settings DocType exists", frappe.db.exists("DocType", SETTINGS), SETTINGS)
    add("Preset DocType exists", frappe.db.exists("DocType", PRESET), PRESET)
    add("Frappe Standard preset exists", frappe.db.exists(PRESET, BASELINE_PRESET), BASELINE_PRESET)
    status = baseline_status() if all(row["passed"] for row in checks[:2]) else {}
    add("Custom theme disabled", status.get("enabled") == 0, status.get("enabled"))
    add("Frappe Standard active", status.get("active_preset") == BASELINE_PRESET, status.get("active_preset"))
    add("Language action enabled", status.get("show_language_action") == 1, status.get("show_language_action"))
    settings = frappe.get_single(SETTINGS) if frappe.db.exists("DocType", SETTINGS) else None
    duplicates = []
    seen = set()
    if settings:
        for row in settings.get("quick_create_items") or []:
            if row.reference_doctype in seen:
                duplicates.append(row.reference_doctype)
            seen.add(row.reference_doctype)
    add("Quick Create rows unique", not duplicates, duplicates)
    failures = [row for row in checks if not row["passed"]]
    return {
        "valid": not failures,
        "checks_total": len(checks),
        "checks_passed": len(checks) - len(failures),
        "checks_failed": len(failures),
        "checks": checks,
        "baseline_version": BASELINE_VERSION,
        "site": frappe.local.site,
        "status": status,
    }


# Compatibility alias for deployment scripts used during the prior theme phase.
def audit_runtime_configuration():
    return audit_frappe_baseline()
