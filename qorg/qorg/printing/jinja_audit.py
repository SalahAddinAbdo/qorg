from __future__ import annotations
import re
import frappe
from frappe.utils.jinja import render_template, validate_template

DOC_PATTERN = re.compile(r"\bdoc(?:\.|\[)")
WINDOW_PATTERN = re.compile(r"\bwindow(?:\.|\[)")


def audit_email_templates():
    results = []
    fields = ["name", "subject", "response"]
    if frappe.get_meta("Email Template").has_field("response_html"):
        fields.append("response_html")
    for row in frappe.get_all("Email Template", fields=fields, limit_page_length=0):
        body = row.get("response_html") or row.get("response") or ""
        item = {
            "name": row.name,
            "uses_doc": bool(DOC_PATTERN.search(body)),
            "uses_window": bool(WINDOW_PATTERN.search(body)),
            "syntax": "passed",
            "preview_without_context": "passed",
            "error": None,
        }
        try:
            validate_template(body)
        except Exception as exc:
            item["syntax"] = "failed"
            item["error"] = str(exc)
            results.append(item)
            continue
        try:
            render_template(body, {})
        except Exception as exc:
            item["preview_without_context"] = "failed"
            item["error"] = str(exc)
        results.append(item)
    return {
        "total": len(results),
        "syntax_failed": [x for x in results if x["syntax"] == "failed"],
        "preview_failed": [x for x in results if x["preview_without_context"] == "failed"],
        "failed": [x for x in results if x["syntax"] == "failed" or x["preview_without_context"] == "failed"],
        "results": results,
    }
