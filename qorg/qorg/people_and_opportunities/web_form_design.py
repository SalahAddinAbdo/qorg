from __future__ import annotations

import hashlib
from pathlib import Path

import frappe
from frappe.utils import cint

CSS_VERSION = "3.0.5"
DEFAULTS = {
    "enabled": 1,
    "company": None,
    "max_width": 1180,
    "header_style": "Hero",
    "hide_child_name": 1,
}


def validate_website_settings(doc, method=None):
    width = cint(doc.get("qorg_web_form_max_content_width") or 1180)
    if width < 760 or width > 1600:
        frappe.throw("Maximum Content Width must be between 760 and 1600 pixels.")


def reconcile_all_web_form_designs(doc=None, method=None, force=False):
    result = {"updated": [], "preserved": []}
    if not frappe.db.exists("DocType", "Web Form"):
        return result

    for name in frappe.get_all("Web Form", pluck="name"):
        web_form = frappe.get_doc("Web Form", name)
        status = apply_managed_design(web_form, force=force, save=True)
        result[status].append(web_form.route or web_form.name)

    frappe.clear_cache(doctype="Web Form")
    return result


def apply_managed_design(doc, method=None, force=False, save=False):
    if not doc.meta.has_field("qorg_web_form_design_mode"):
        return "preserved"

    force = bool(force or cint(doc.get("qorg_apply_managed_web_form_design")))
    expected = build_managed_css(doc)
    current = doc.get("custom_css") or ""
    stored_hash = doc.get("qorg_managed_css_hash") or ""
    managed_current = not current or (
        stored_hash and stored_hash == css_hash(current)
    )

    if force or managed_current:
        doc.custom_css = expected
        doc.qorg_managed_css_version = CSS_VERSION
        doc.qorg_managed_css_hash = css_hash(expected)
        doc.qorg_managed_css_update_available = 0
        doc.qorg_apply_managed_web_form_design = 0
        status = "updated"
    else:
        doc.qorg_managed_css_update_available = int(
            css_hash(expected) != css_hash(current)
        )
        doc.qorg_apply_managed_web_form_design = 0
        status = "preserved"

    if save:
        doc.save(ignore_permissions=True)

    return status


def build_managed_css(web_form):
    settings = _effective_settings(web_form)
    if not settings.enabled:
        return ""

    primary, secondary, accent = _branding(settings.company)
    template_path = (
        Path(__file__).resolve().parent
        / "data"
        / "web_form_design_v3.css"
    )
    template = template_path.read_text(encoding="utf-8")
    css = (
        template.replace("__PRIMARY__", primary)
        .replace("__SECONDARY__", secondary)
        .replace("__ACCENT__", accent)
        .replace("__MAX_WIDTH__", str(settings.max_width))
    )

    return css + "\n" + _header_css(
        settings.header_style,
        primary,
        secondary,
        accent,
    )


def _effective_settings(web_form):
    values = frappe._dict(DEFAULTS.copy())
    website = frappe.get_single("Website Settings")

    mapping = {
        "enabled": "qorg_enable_enhanced_web_form_design",
        "company": "qorg_web_form_default_company",
        "max_width": "qorg_web_form_max_content_width",
        "header_style": "qorg_web_form_header_style",
        "hide_child_name": "qorg_web_form_hide_child_row_name",
    }

    for key, fieldname in mapping.items():
        if (
            website.meta.has_field(fieldname)
            and website.get(fieldname) not in (None, "")
        ):
            values[key] = website.get(fieldname)

    mode = web_form.get("qorg_web_form_design_mode") or "Use Global Setting"
    if mode == "Enhanced Design":
        values.enabled = 1
    elif mode == "Standard Frappe Design":
        values.enabled = 0

    values.company = (
        web_form.get("qorg_web_form_branding_company")
        or values.company
    )

    width = cint(web_form.get("qorg_web_form_max_content_width_override"))
    if width:
        if width < 760 or width > 1600:
            frappe.throw(
                "Maximum Content Width Override must be between 760 and 1600 pixels."
            )
        values.max_width = width

    override = web_form.get("qorg_web_form_header_style_override")
    if override and override != "Use Global Setting":
        values.header_style = override

    values.enabled = cint(values.enabled)
    values.max_width = min(
        max(cint(values.max_width) or 1180, 760),
        1600,
    )
    values.company = (
        values.company
        or frappe.defaults.get_global_default("company")
    )
    values.header_style = values.header_style or "Hero"
    return values


def _header_css(style, primary, secondary, accent):
    outer = "main.container .web-form-header"
    inner = "main.container .web-form-header .web-form-head"
    title = "main.container .web-form-header .web-form-head h1"
    introduction = (
        "main.container .web-form-header "
        ".web-form-head .web-form-introduction"
    )
    status = (
        "main.container .web-form-header .web-form-head .indicator-pill, "
        "main.container .web-form-header .web-form-head .es-badge"
    )

    reset = f"""
{outer} {{
  display: block !important;
  width: 100%;
  transform: none;
  clip-path: none;
}}

{outer}::before,
{outer}::after,
{inner}::before,
{inner}::after {{
  content: none !important;
  display: none !important;
}}

{inner} {{
  display: block !important;
  width: 100% !important;
  margin: 0 !important;
  transform: none !important;
  clip-path: none !important;
}}

{inner} > .title {{
  display: flex !important;
  align-items: center !important;
  flex-wrap: wrap !important;
  gap: 10px 14px !important;
  margin: 0 !important;
}}

{inner} .web-form-title {{
  min-width: 0 !important;
  max-width: 100% !important;
  overflow: visible !important;
}}
"""

    if style == "Standard":
        return reset + f"""
{outer} {{
  margin: 22px 0 18px !important;
  padding: 0 !important;
  color: #102a34 !important;
  background: transparent !important;
  border: 0 !important;
  box-shadow: none !important;
  overflow: visible !important;
}}

{inner} {{
  padding: 0 0 18px !important;
  color: #102a34 !important;
  background: transparent !important;
  border: 0 !important;
  border-bottom: 2px solid {primary} !important;
  border-radius: 0 !important;
  box-shadow: none !important;
  overflow: visible !important;
}}

{title} {{
  margin: 0 !important;
  color: #102a34 !important;
  font-size: clamp(1.75rem, 3.2vw, 2.45rem) !important;
  font-weight: 800 !important;
  line-height: 1.12 !important;
  white-space: normal !important;
  overflow: visible !important;
  text-overflow: clip !important;
}}

{introduction} {{
  max-width: 76ch !important;
  margin: 14px 0 0 !important;
  padding: 0 !important;
  color: #435660 !important;
  background: transparent !important;
  border: 0 !important;
  box-shadow: none !important;
  line-height: 1.65 !important;
}}
"""

    return reset + f"""
{outer} {{
  margin: 22px 0 18px !important;
  padding: clamp(26px, 3.4vw, 42px)
           clamp(26px, 4vw, 54px) !important;
  color: #ffffff !important;
  background: linear-gradient(
    135deg,
    {secondary} 0%,
    {primary} 58%,
    {secondary} 100%
  ) !important;
  border: 0 !important;
  border-radius: 18px !important;
  box-shadow: 0 18px 42px rgba(23, 74, 91, .18) !important;
  overflow: hidden !important;
}}

{inner} {{
  padding: 0 !important;
  color: inherit !important;
  background: transparent !important;
  border: 0 !important;
  border-radius: 0 !important;
  box-shadow: none !important;
  overflow: visible !important;
}}

{title} {{
  margin: 0 !important;
  color: #ffffff !important;
  font-size: clamp(2rem, 4vw, 3rem) !important;
  font-weight: 800 !important;
  line-height: 1.08 !important;
  letter-spacing: -.035em !important;
  white-space: normal !important;
  overflow: visible !important;
  text-overflow: clip !important;
}}

{introduction} {{
  max-width: 76ch !important;
  margin: 16px 0 0 !important;
  padding: 0 !important;
  color: rgba(255, 255, 255, .92) !important;
  background: transparent !important;
  border: 0 !important;
  border-radius: 0 !important;
  box-shadow: none !important;
  font-size: clamp(1rem, 1.5vw, 1.15rem) !important;
  line-height: 1.65 !important;
}}

{status} {{
  position: relative !important;
  margin: 0 !important;
  padding: 4px 10px !important;
  color: #6f4f00 !important;
  background: #fff2c6 !important;
  border: 1px solid rgba(217, 166, 46, .45) !important;
  border-radius: 999px !important;
  box-shadow: none !important;
}}

main.container form.web-form {{
  margin-top: 0 !important;
}}

@media (min-width: 768px) and (max-width: 1199px) {{
  {outer} {{
    margin-top: 18px !important;
    padding: 30px 34px !important;
    border-radius: 16px !important;
  }}
}}

@media (max-width: 767px) {{
  {outer} {{
    margin: 8px 0 12px !important;
    padding: 22px 18px !important;
    border-radius: 13px !important;
    box-shadow: 0 10px 28px rgba(23, 74, 91, .16) !important;
  }}

  {title} {{
    font-size: clamp(1.65rem, 8vw, 2.2rem) !important;
  }}

  {introduction} {{
    margin-top: 12px !important;
    font-size: .98rem !important;
    line-height: 1.55 !important;
  }}
}}
"""


def _branding(company):
    defaults = ("#176b87", "#084b59", "#d9a62e")
    if not company or not frappe.db.exists("Company", company):
        return defaults

    doc = frappe.get_cached_doc("Company", company)

    def value(*names):
        for name in names:
            if doc.meta.has_field(name) and doc.get(name):
                return doc.get(name)
        return None

    return (
        value(
            "custom_print_primary_color",
            "custom_print_document_header_color",
        )
        or defaults[0],
        value(
            "custom_print_document_header_color",
            "custom_print_primary_color",
        )
        or defaults[1],
        value("custom_print_accent_color") or defaults[2],
    )


def css_hash(value):
    return hashlib.sha256(
        (value or "").encode("utf-8")
    ).hexdigest()
