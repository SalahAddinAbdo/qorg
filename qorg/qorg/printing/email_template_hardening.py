from __future__ import annotations
import re
import frappe
from frappe.utils.jinja import validate_template

MARKER = "<!-- qorg-context-safe:v1 -->"
DOC_REF = re.compile(r"\bdoc(?:\.|\[)")
WINDOW_REF = re.compile(r"\bwindow(?:\.|\[)")


def _wrap(body: str) -> tuple[str, list[str]]:
    body = body or ""
    if MARKER in body:
        return body, []
    required = []
    guards = []
    if DOC_REF.search(body):
        required.append("doc")
        guards.append("doc is defined")
    if WINDOW_REF.search(body):
        required.append("window")
        guards.append("window is defined")
    if not guards:
        return body, []
    condition = " and ".join(guards)
    fallback = (
        "<div style='font-family:Arial,sans-serif;line-height:1.6'>"
        "<p><strong>Template preview requires document context.</strong></p>"
        "<p dir='rtl' style='text-align:right'><strong>تتطلب معاينة القالب سياق المستند.</strong></p>"
        "</div>"
    )
    wrapped = f"{MARKER}\n{{% if {condition} %}}\n{body}\n{{% else %}}\n{fallback}\n{{% endif %}}"
    validate_template(wrapped)
    return wrapped, required


def harden_email_template_previews():
    """Make every stored Email Template preview-safe without changing runtime output.

    The original template remains byte-for-byte inside a Jinja context guard. Database
    values are updated directly to avoid HTML sanitization rewriting Jinja quotes.
    """
    result = {"updated": [], "already_safe": [], "no_context_dependency": [], "failed": []}
    meta = frappe.get_meta("Email Template")
    has_html = meta.has_field("response_html")
    fields = ["name", "response"] + (["response_html"] if has_html else [])
    for row in frappe.get_all("Email Template", fields=fields, limit_page_length=0):
        changed = False
        required = set()
        values = {}
        for field in ("response", "response_html"):
            if field not in row or not row.get(field):
                continue
            try:
                wrapped, deps = _wrap(row.get(field))
            except Exception as exc:
                result["failed"].append({"name": row.name, "field": field, "error": str(exc)})
                continue
            required.update(deps)
            if wrapped != row.get(field):
                values[field] = wrapped
                changed = True
        if changed:
            frappe.db.set_value("Email Template", row.name, values, update_modified=False)
            result["updated"].append({"name": row.name, "contexts": sorted(required)})
        elif MARKER in (row.get("response_html") or row.get("response") or ""):
            result["already_safe"].append(row.name)
        else:
            result["no_context_dependency"].append(row.name)
    frappe.clear_cache(doctype="Email Template")
    return result
