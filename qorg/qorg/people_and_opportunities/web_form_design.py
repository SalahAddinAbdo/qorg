from __future__ import annotations

import hashlib
from pathlib import Path

import frappe
from frappe.utils import cint

CSS_VERSION = "3.0.0"
DEFAULTS = {"enabled": 1, "company": None, "max_width": 1180, "header_style": "Hero", "hide_child_name": 1}


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
    managed_current = not current or (stored_hash and stored_hash == css_hash(current))
    if force or managed_current:
        doc.custom_css = expected
        doc.qorg_managed_css_version = CSS_VERSION
        doc.qorg_managed_css_hash = css_hash(expected)
        doc.qorg_managed_css_update_available = 0
        doc.qorg_apply_managed_web_form_design = 0
        status = "updated"
    else:
        doc.qorg_managed_css_update_available = int(css_hash(expected) != css_hash(current))
        status = "preserved"
    if save:
        doc.save(ignore_permissions=True)
    return status


def build_managed_css(web_form):
    settings = _effective_settings(web_form)
    if not settings.enabled:
        return ""
    primary, secondary, accent = _branding(settings.company)
    template = (Path(__file__).resolve().parent / "data" / "web_form_design_v3.css").read_text(encoding="utf-8")
    css = (template.replace("__PRIMARY__", primary)
                   .replace("__SECONDARY__", secondary)
                   .replace("__ACCENT__", accent)
                   .replace("__MAX_WIDTH__", str(settings.max_width)))
    return css + "\n" + _header_css(settings.header_style, primary, secondary, accent)


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
        if website.meta.has_field(fieldname) and website.get(fieldname) not in (None, ""):
            values[key] = website.get(fieldname)

    mode = web_form.get("qorg_web_form_design_mode") or "Use Global Setting"
    if mode == "Enhanced Design": values.enabled = 1
    elif mode == "Standard Frappe Design": values.enabled = 0
    values.company = web_form.get("qorg_web_form_branding_company") or values.company
    width = cint(web_form.get("qorg_web_form_max_content_width_override"))
    if width:
        if width < 760 or width > 1600: frappe.throw("Maximum Content Width Override must be between 760 and 1600 pixels.")
        values.max_width = width
    override = web_form.get("qorg_web_form_header_style_override")
    if override and override != "Use Global Setting": values.header_style = override
    values.enabled = cint(values.enabled)
    values.max_width = min(max(cint(values.max_width) or 1180, 760), 1600)
    values.company = values.company or frappe.defaults.get_global_default("company")
    values.header_style = values.header_style or "Hero"
    return values


def _header_css(style, primary, secondary, accent):
    common = '''main.container > .web-form-header, main.container > .page-header { margin: 22px 0 0; }\n'''
    if style == "Standard":
        return common + f'''main.container > .web-form-header, main.container > .page-header {{ padding: 0 0 18px; background: transparent; border-bottom: 2px solid {primary}; }}\nmain.container > .web-form-header h1, main.container > .page-header h1 {{ color: #102a34; font-size: clamp(1.75rem,3.2vw,2.45rem); }}'''
    return common + f'''main.container > .web-form-header, main.container > .page-header {{ position: relative; overflow: hidden; padding: clamp(24px,4vw,46px); color: #fff; background: linear-gradient(135deg,{secondary},{primary}); border: 0; border-radius: 18px; box-shadow: 0 18px 44px rgba(8,75,89,.20); }}\nmain.container > .web-form-header::after, main.container > .page-header::after {{ content: ""; position: absolute; inset-inline-end: -65px; bottom: -100px; width: 220px; height: 220px; border: 34px solid rgba(255,255,255,.08); border-radius: 50%; pointer-events: none; }}\nmain.container > .web-form-header h1, main.container > .page-header h1 {{ position: relative; z-index: 1; margin: 0; color: #fff; font-size: clamp(1.8rem,4vw,2.7rem); }}\nmain.container > .web-form-introduction, main.container > .introduction {{ margin-top: -1px; border-inline-start-color: {accent}; }}'''


def _branding(company):
    defaults = ("#0b6477", "#084b59", "#d9a62e")
    if not company or not frappe.db.exists("Company", company): return defaults
    doc = frappe.get_cached_doc("Company", company)
    def value(*names):
        for name in names:
            if doc.meta.has_field(name) and doc.get(name): return doc.get(name)
    return (value("custom_print_primary_color", "custom_print_document_header_color") or defaults[0],
            value("custom_print_document_header_color", "custom_print_primary_color") or defaults[1],
            value("custom_print_accent_color") or defaults[2])


def css_hash(value):
    return hashlib.sha256((value or "").encode("utf-8")).hexdigest()
