import re

import frappe

from .meta_audit import _runtime_versions


REQUIRED_MAJOR_VERSIONS = {
    "frappe": 16,
    "erpnext": 16,
    "hrms": 16,
}


def runtime_versions():
    """Return a normalized app -> version string mapping on Frappe 16."""
    raw = _runtime_versions() or {}
    normalized = {}
    for app, value in raw.items():
        if isinstance(value, dict):
            normalized[app] = str(value.get("version") or value.get("branch") or "")
        else:
            normalized[app] = str(value or "")
    return normalized


def _major(version):
    match = re.search(r"(?:^|[^0-9])(\d+)(?:\.|$)", str(version or ""))
    return int(match.group(1)) if match else None


def validate_runtime():
    """Return compatibility issues without failing migrate/runtime acceptance."""
    versions = runtime_versions()
    issues = []

    for app, required_major in REQUIRED_MAJOR_VERSIONS.items():
        version = versions.get(app)
        if not version:
            issues.append(
                {
                    "code": "APP_VERSION_UNAVAILABLE",
                    "severity": "Warning",
                    "app": app,
                    "message": f"The installed version of {app} could not be determined.",
                }
            )
            continue

        major = _major(version)
        if major is None:
            issues.append(
                {
                    "code": "APP_VERSION_UNPARSEABLE",
                    "severity": "Warning",
                    "app": app,
                    "installed_version": version,
                    "message": f"The installed version of {app} could not be parsed: {version}.",
                }
            )
        elif major != required_major:
            issues.append(
                {
                    "code": "APP_MAJOR_VERSION_MISMATCH",
                    "severity": "Error",
                    "app": app,
                    "installed_version": version,
                    "required_major": required_major,
                    "message": f"{app} major version {required_major} is required; installed version is {version}.",
                }
            )

    if not frappe.db.exists("DocType", "Payroll Entry"):
        issues.append(
            {
                "code": "PAYROLL_ENTRY_MISSING",
                "severity": "Error",
                "message": "Payroll Entry DocType is not installed.",
            }
        )

    return issues
