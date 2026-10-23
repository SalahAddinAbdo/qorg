from __future__ import annotations

import hashlib
import json

import frappe
from frappe.utils import now_datetime

# Print Format is deliberately excluded. Print formats are configuration records,
# not navigation/interface components to hide or restrict from this control center.
SPECS = (
    ("Report", "Report", "name", "report_name", "module", "ref_doctype"),
    ("Page", "Page", "name", "page_name", "module", None),
    ("Workspace", "Workspace", "name", "label", "module", None),
    ("Dashboard", "Dashboard", "name", "dashboard_name", "module", None),
    ("Number Card", "Number Card", "name", "label", "module", "document_type"),
    ("Web Form", "Web Form", "name", "title", "module", "doc_type"),
    ("Web Page", "Web Page", "name", "title", None, None),
)


def scan_interface_components():
    result = []
    synchronized_on = now_datetime()
    for kind, doctype, name_field, label_field, module_field, reference_field in SPECS:
        if not frappe.db.exists("DocType", doctype):
            continue
        meta = frappe.get_meta(doctype)
        fields = [name_field]
        for fieldname in (label_field, module_field, reference_field):
            if fieldname and meta.has_field(fieldname) and fieldname not in fields:
                fields.append(fieldname)
        for row in frappe.get_all(doctype, fields=fields, order_by=f"{name_field} asc"):
            name = row.get(name_field)
            module = row.get(module_field) if module_field else ""
            app = frappe.db.get_value("Module Def", module, "app_name") if module else ""
            data = {
                "component_type": kind,
                "component_name": name,
                "component_label": row.get(label_field) if label_field in fields else name,
                "app_name": app or "",
                "module_name": module or "",
                "reference_doctype": row.get(reference_field) if reference_field and reference_field in fields else "",
                "current_visibility": "Visible",
                "requested_visibility": "Visible",
                "risk_level": "High" if app in ("frappe", "erpnext", "hrms") else "Low",
                "last_synchronized_on": synchronized_on,
            }
            data["scan_fingerprint"] = hashlib.sha256(json.dumps(data, default=str, sort_keys=True).encode()).hexdigest()
            result.append(data)
    return result
