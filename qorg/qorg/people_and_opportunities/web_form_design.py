from __future__ import annotations

import hashlib

import frappe
from frappe.utils import cint

CSS_VERSION = "2.1.0"
DEFAULTS = {
    "enabled": 1,
    "use_company_branding": 1,
    "company": None,
    "max_width": 1180,
    "emphasize_header": 1,
    "emphasize_introduction": 1,
    "sticky_actions": 0,
    "hide_child_name": 1,
}


def validate_website_settings(doc, method=None):
    width = cint(doc.get("qorg_web_form_max_content_width") or 1180)
    if width < 760 or width > 1600:
        frappe.throw("Maximum Content Width must be between 760 and 1600 pixels.")


def reconcile_all_web_form_designs(doc=None, method=None, force=False):
    if not frappe.db.exists("DocType", "Web Form"):
        return {"updated": [], "preserved": []}
    result = {"updated": [], "preserved": []}
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
    current_hash = css_hash(current)
    managed_current = not current or (stored_hash and stored_hash == current_hash)

    if force or managed_current:
        doc.custom_css = expected
        doc.qorg_managed_css_version = CSS_VERSION
        doc.qorg_managed_css_hash = css_hash(expected)
        doc.qorg_managed_css_update_available = 0
        doc.qorg_apply_managed_web_form_design = 0
        status = "updated"
    else:
        doc.qorg_managed_css_update_available = int(css_hash(expected) != current_hash)
        doc.qorg_apply_managed_web_form_design = 0
        status = "preserved"

    if save:
        doc.save(ignore_permissions=True)
    return status


def build_managed_css(web_form):
    settings = get_effective_design_settings(web_form)
    if not settings.enabled:
        return ""

    primary, secondary, accent, surface, _logo = _branding(settings.company)
    header_css = _header_css(primary, secondary) if settings.emphasize_header else ""
    intro_css = _introduction_css(accent) if settings.emphasize_introduction else ""
    sticky_css = _sticky_actions_css() if settings.sticky_actions else ""
    child_css = _child_name_css() if settings.hide_child_name else ""

    return f'''/* QOrg managed Web Form CSS v{CSS_VERSION}. No JavaScript required. */
:root {{
  --qwf-primary: {primary};
  --qwf-secondary: {secondary};
  --qwf-accent: {accent};
  --qwf-surface: {surface};
  --qwf-page: #f4f7f9;
  --qwf-text: #1f2f3a;
  --qwf-muted: #687985;
  --qwf-border: #dbe4e8;
  --qwf-input: #f4f7f9;
  --qwf-ring: rgba(23, 107, 135, .14);
  --qwf-max-width: {settings.max_width}px;
}}
body {{ background: var(--qwf-page); }}
main .container, .page-content-wrapper > .container {{
  width: min(100% - 2rem, var(--qwf-max-width));
  max-width: var(--qwf-max-width);
  margin-inline: auto;
}}
.web-form-wrapper, .web-form-container {{
  width: 100%;
  margin: clamp(1rem, 3vw, 2.5rem) auto;
  padding: clamp(1rem, 3.2vw, 2.75rem);
  color: var(--qwf-text);
  background: var(--qwf-surface);
  border: 1px solid var(--qwf-border);
  border-radius: 20px;
  box-shadow: 0 16px 48px rgba(31, 47, 58, .09);
}}
.form-section, .web-form-section {{ margin: 1.15rem 0; padding: clamp(1rem, 2.2vw, 1.45rem); background: #fff; border: 1px solid var(--qwf-border); border-radius: 14px; }}
.section-head, .section-title {{ margin-bottom: .95rem; color: var(--qwf-secondary); font-size: 1.05rem; font-weight: 750; }}
.form-group {{ margin-bottom: 1.05rem; }}
.control-label, .form-label {{ display: inline-block; margin-bottom: .42rem; color: var(--qwf-text); font-size: .91rem; font-weight: 700; }}
.help-box, .form-text, .description {{ margin-top: .35rem; color: var(--qwf-muted); font-size: .8rem; line-height: 1.5; }}
.form-control, .input-with-feedback, .awesomplete > input {{ min-height: 46px; padding-inline: .9rem; color: var(--qwf-text); background: var(--qwf-input); border: 1px solid transparent; border-radius: 9px; box-shadow: none; transition: background .16s ease, border-color .16s ease, box-shadow .16s ease; }}
textarea.form-control {{ min-height: 132px; padding-top: .78rem; line-height: 1.65; resize: vertical; }}
.form-control:hover, .awesomplete > input:hover {{ border-color: var(--qwf-border); }}
.form-control:focus, .awesomplete > input:focus, .ql-container:focus-within {{ color: var(--qwf-text); background: #fff; border-color: var(--qwf-primary); box-shadow: 0 0 0 4px var(--qwf-ring); }}
.form-control[readonly], .form-control:disabled {{ color: #53636e; background: #eef2f4; opacity: 1; }}
.ql-toolbar {{ background: #f7f9fa; border-color: var(--qwf-border) !important; border-radius: 10px 10px 0 0; }}
.ql-container {{ min-height: 180px; background: #fff; border-color: var(--qwf-border) !important; border-radius: 0 0 10px 10px; }}
.form-grid, .grid-field {{ overflow: hidden; background: #fff; border: 1px solid var(--qwf-border); border-radius: 12px; }}
.grid-heading-row {{ color: var(--qwf-secondary); background: #eef5f7; font-weight: 700; }}
.grid-row:hover .data-row {{ background: #f8fafb; }}
.grid-add-row {{ margin: .7rem; color: var(--qwf-primary); background: #eef6f8; border: 1px dashed #bfd6de; border-radius: 8px; font-weight: 650; }}
.grid-row-form {{ padding: 1rem; background: #f8fafb; border: 1px solid var(--qwf-border); border-radius: 12px; }}
.btn {{ min-height: 42px; border-radius: 9px; font-weight: 650; }}
.btn-primary {{ color: #fff; background: var(--qwf-primary); border-color: var(--qwf-primary); box-shadow: 0 7px 18px rgba(23, 107, 135, .17); }}
.btn-primary:hover, .btn-primary:focus {{ color: #fff; background: var(--qwf-secondary); border-color: var(--qwf-secondary); }}
.web-form-actions .btn-primary, .form-actions .btn-primary {{ min-width: min(100%, 220px); padding-inline: 1.35rem; }}
{header_css}
{intro_css}
{sticky_css}
{child_css}
@media (min-width: 768px) and (max-width: 1199px) {{ main .container, .page-content-wrapper > .container {{ width: min(100% - 3rem, var(--qwf-max-width)); }} }}
@media (max-width: 767px) {{
  main .container, .page-content-wrapper > .container {{ width: min(100% - 1rem, var(--qwf-max-width)); }}
  .web-form-wrapper, .web-form-container {{ margin: .65rem auto 1.25rem; padding: 1rem; border-radius: 14px; box-shadow: 0 8px 24px rgba(31, 47, 58, .07); }}
  .form-section, .web-form-section {{ padding: .9rem; border-radius: 11px; }}
  .form-control, .input-with-feedback, .awesomplete > input {{ min-height: 44px; }}
  .web-form-actions, .form-actions {{ display: grid; grid-template-columns: 1fr; gap: .55rem; }}
  .web-form-actions .btn, .form-actions .btn {{ width: 100%; }}
}}
@media (max-width: 379px) {{ main .container, .page-content-wrapper > .container {{ width: calc(100% - .75rem); }} .web-form-wrapper, .web-form-container {{ padding: .82rem; }} }}
@media (prefers-reduced-motion: reduce) {{ .form-control, .input-with-feedback, .awesomplete > input {{ transition: none; }} }}
'''.strip()

def get_effective_design_settings(web_form):
    values = frappe._dict(DEFAULTS.copy())
    website = frappe.get_single("Website Settings")
    mapping = {
        "enabled": "qorg_enable_enhanced_web_form_design",
        "use_company_branding": "qorg_web_form_use_company_branding",
        "company": "qorg_web_form_default_company",
        "max_width": "qorg_web_form_max_content_width",
        "emphasize_header": "qorg_web_form_emphasize_header",
        "emphasize_introduction": "qorg_web_form_emphasize_introduction",
        "sticky_actions": "qorg_web_form_sticky_actions",
        "hide_child_name": "qorg_web_form_hide_child_row_name",
    }
    for key, fieldname in mapping.items():
        if website.meta.has_field(fieldname) and website.get(fieldname) is not None:
            values[key] = website.get(fieldname)

    mode = web_form.get("qorg_web_form_design_mode") or "Use Global Setting"
    if mode == "Enhanced Design":
        values.enabled = 1
    elif mode == "Standard Frappe Design":
        values.enabled = 0

    values.company = web_form.get("qorg_web_form_branding_company") or values.company
    override_width = cint(web_form.get("qorg_web_form_max_content_width_override"))
    if override_width:
        if override_width < 760 or override_width > 1600:
            frappe.throw("Maximum Content Width Override must be between 760 and 1600 pixels.")
        values.max_width = override_width

    values.emphasize_header = _choice(web_form.get("qorg_web_form_header_mode"), values.emphasize_header, "Emphasize", "Standard")
    values.emphasize_introduction = _choice(web_form.get("qorg_web_form_introduction_mode"), values.emphasize_introduction, "Emphasize", "Standard")
    values.sticky_actions = _choice(web_form.get("qorg_web_form_sticky_actions_mode"), values.sticky_actions, "Enable", "Disable")
    values.hide_child_name = _choice(web_form.get("qorg_web_form_child_name_mode"), values.hide_child_name, "Hide", "Show")

    for key in ("enabled", "use_company_branding", "emphasize_header", "emphasize_introduction", "sticky_actions", "hide_child_name"):
        values[key] = cint(values[key])
    values.max_width = min(max(cint(values.max_width) or 1180, 760), 1600)
    if not values.company:
        values.company = frappe.defaults.get_global_default("company")
    return values


def css_hash(value):
    return hashlib.sha256((value or "").encode("utf-8")).hexdigest()


def _choice(value, inherited, enabled, disabled):
    if value == enabled:
        return 1
    if value == disabled:
        return 0
    return inherited


def _branding(company):
    default = ("#176b87", "#0d4f67", "#2f855a", "#ffffff", None)
    if not company or not frappe.db.exists("Company", company):
        return default
    doc = frappe.get_cached_doc("Company", company)

    def value(*names):
        for name in names:
            if doc.meta.has_field(name) and doc.get(name):
                return doc.get(name)
        return None

    return (
        value("custom_print_primary_color", "custom_print_document_header_color") or default[0],
        value("custom_print_document_header_color", "custom_print_primary_color") or default[1],
        value("custom_print_accent_color") or default[2],
        value("custom_print_light_color") or default[3],
        value("company_logo", "custom_company_logo", "custom_print_logo"),
    )


def _header_css(primary, secondary):
    return f'''.web-form-header, .web-form-head {{
  position: relative;
  overflow: hidden;
  margin: 0 0 1.2rem;
  padding: clamp(1.25rem, 3vw, 2rem);
  color: #fff;
  background: linear-gradient(135deg, {secondary}, {primary});
  border: 0;
  border-radius: 16px;
  box-shadow: 0 12px 30px rgba(31, 47, 58, .12);
}}
.web-form-header::after, .web-form-head::after {{ content: ""; position: absolute; inset-inline-end: -55px; bottom: -85px; width: 180px; height: 180px; border: 28px solid rgba(255, 255, 255, .08); border-radius: 50%; pointer-events: none; }}
.web-form-header h1, .web-form-head h1 {{ position: relative; z-index: 1; margin: 0; color: #fff; font-size: clamp(1.55rem, 4vw, 2.35rem); line-height: 1.18; letter-spacing: -.025em; }}
.page-header {{ background: transparent; }}'''

def _introduction_css(accent):
    return f'''.web-form-introduction, .introduction {{
  margin: .9rem 0 1.2rem;
  padding: .9rem 1rem;
  color: #40515c;
  background: #f6faf8;
  border-inline-start: 4px solid {accent};
  border-radius: 10px;
  line-height: 1.6;
}}'''


def _sticky_actions_css():
    return '''.web-form-actions, .form-actions {
  position: sticky;
  bottom: .5rem;
  z-index: 5;
  margin-top: 1rem;
  padding: .8rem;
  background: rgba(255,255,255,.94);
  border: 1px solid var(--qwf-border);
  border-radius: 12px;
  box-shadow: 0 10px 28px rgba(34,52,64,.12);
}'''


def _child_name_css():
    return '''.grid-row-form [data-fieldname="name"],
.grid-row-form .form-group[data-fieldname="name"] { display: none !important; }'''
