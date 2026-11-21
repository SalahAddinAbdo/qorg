from __future__ import annotations
from packaging.version import Version
import frappe
MINIMUM={"frappe":"16.53.0","erpnext":"16.52.1","hrms":"16.52.0"}
def runtime_versions():
    data=frappe.get_versions() or {};return {k:(v.get("version") if isinstance(v,dict) else str(v)) for k,v in data.items()}
def validate_runtime():
    versions=runtime_versions();issues=[]
    for app,minimum in MINIMUM.items():
        version=versions.get(app)
        if not version: issues.append(f"Missing required app: {app}");continue
        try:
            if Version(version)<Version(minimum):issues.append(f"{app} {version} is below required {minimum}")
        except Exception: issues.append(f"Unable to compare {app} version {version}")
    return issues
