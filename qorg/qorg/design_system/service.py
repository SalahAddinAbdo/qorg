import json
import re
from urllib.parse import urlparse

import frappe

SETTINGS = "Q Org Design System Settings"
HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")
FONT_NAME_RE = re.compile(r"^[\w .,'-]{1,120}$", re.UNICODE)

DEFAULTS = {
    "primary_color": "#137690",
    "secondary_color": "#CBAE66",
    "page_background_color": "#FFFFFF",
    "surface_color": "#FFFFFF",
    "control_background_color": "#F4F5F6",
    "primary_text_color": "#1F272E",
    "muted_text_color": "#687178",
    "border_color": "#DFE2E5",
    "border_radius": 4,
    "large_border_radius": 8,
    "font_size_xs": 11,
    "font_size_sm": 12,
    "font_size_base": 14,
    "font_size_lg": 16,
    "font_size_h6": 14,
    "font_size_h5": 16,
    "font_size_h4": 18,
    "font_size_h3": 20,
    "font_size_h2": 24,
    "font_size_h1": 32,
    "font_size_display": 48,
    "body_line_height": 1.35,
    "paragraph_line_height": 1.55,
    "heading_line_height": 1.25,
}


def _value(doc, fieldname):
    return doc.get(fieldname) if doc.meta.has_field(fieldname) else None


def _color(doc, fieldname):
    value = str(_value(doc, fieldname) or DEFAULTS[fieldname]).strip()
    return value.upper() if HEX_RE.fullmatch(value) else DEFAULTS[fieldname]


def _int(doc, fieldname, minimum, maximum):
    try:
        value = int(_value(doc, fieldname) or DEFAULTS[fieldname])
    except (TypeError, ValueError):
        value = DEFAULTS[fieldname]
    return max(minimum, min(maximum, value))


def _float(doc, fieldname, minimum, maximum):
    try:
        value = float(_value(doc, fieldname) or DEFAULTS[fieldname])
    except (TypeError, ValueError):
        value = DEFAULTS[fieldname]
    return max(minimum, min(maximum, value))


def _font_stack(doc, language=None):
    source = _value(doc, "font_source") or "Frappe Default"
    if source == "Frappe Default":
        return None
    primary = str(_value(doc, "primary_font_family") or "").strip()
    arabic = str(_value(doc, "arabic_font_family") or "").strip()
    fallback = str(_value(doc, "fallback_font_family") or 'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif').strip()
    names = [arabic, primary] if str(language or "").lower().startswith("ar") else [primary, arabic]
    quoted = [f'"{name}"' for name in names if name and FONT_NAME_RE.fullmatch(name)]
    return ", ".join(quoted + [fallback])


def get_ui_tokens(language=None):
    doc = frappe.get_single(SETTINGS)
    tokens = {
        "primary_color": _color(doc, "primary_color"),
        "secondary_color": _color(doc, "secondary_color"),
        "page_background_color": _color(doc, "page_background_color"),
        "surface_color": _color(doc, "surface_color"),
        "control_background_color": _color(doc, "control_background_color"),
        "primary_text_color": _color(doc, "primary_text_color"),
        "muted_text_color": _color(doc, "muted_text_color"),
        "border_color": _color(doc, "border_color"),
        "border_radius": _int(doc, "border_radius", 0, 32),
        "large_border_radius": _int(doc, "large_border_radius", 0, 48),
        "font_size_xs": _int(doc, "font_size_xs", 10, 20),
        "font_size_sm": _int(doc, "font_size_sm", 10, 22),
        "font_size_base": _int(doc, "font_size_base", 11, 24),
        "font_size_lg": _int(doc, "font_size_lg", 12, 28),
        "font_size_h6": _int(doc, "font_size_h6", 12, 32),
        "font_size_h5": _int(doc, "font_size_h5", 12, 36),
        "font_size_h4": _int(doc, "font_size_h4", 14, 42),
        "font_size_h3": _int(doc, "font_size_h3", 16, 48),
        "font_size_h2": _int(doc, "font_size_h2", 18, 60),
        "font_size_h1": _int(doc, "font_size_h1", 20, 72),
        "font_size_display": _int(doc, "font_size_display", 24, 96),
        "body_line_height": _float(doc, "body_line_height", 1.0, 2.0),
        "paragraph_line_height": _float(doc, "paragraph_line_height", 1.0, 2.0),
        "heading_line_height": _float(doc, "heading_line_height", 1.0, 2.0),
    }
    tokens["font_family"] = _font_stack(doc, language)
    return tokens


def get_font_stylesheet_url():
    doc = frappe.get_single(SETTINGS)
    source = _value(doc, "font_source") or "Frappe Default"
    url = str(_value(doc, "font_stylesheet_url") or "").strip()
    if source not in ("Google Fonts", "Custom Web Font") or not url:
        return None
    parsed = urlparse(url)
    if parsed.scheme != "https":
        return None
    if source == "Google Fonts" and parsed.netloc not in ("fonts.googleapis.com", "fonts.gstatic.com"):
        return None
    return url


def tokens_to_css(tokens=None):
    t = tokens or get_ui_tokens(getattr(frappe.local, "lang", None))
    values = {
        "--primary-color": t["primary_color"],
        "--brand-color": t["primary_color"],
        "--qorg-secondary-color": t["secondary_color"],
        "--bg-color": t["page_background_color"],
        "--fg-color": t["surface_color"],
        "--card-bg": t["surface_color"],
        "--control-bg": t["control_background_color"],
        "--text-color": t["primary_text_color"],
        "--text-muted": t["muted_text_color"],
        "--border-color": t["border_color"],
        "--light-border-color": t["border_color"],
        "--border-radius": f'{t["border_radius"]}px',
        "--border-radius-lg": f'{t["large_border_radius"]}px',
        "--card-border-radius": f'{t["large_border_radius"]}px',
        "--font-size-xs": f'{t["font_size_xs"]}px',
        "--font-size-sm": f'{t["font_size_sm"]}px',
        "--font-size-base": f'{t["font_size_base"]}px',
        "--font-size-lg": f'{t["font_size_lg"]}px',
        "--font-size-xl": f'{t["font_size_h4"]}px',
        "--font-size-2xl": f'{t["font_size_h3"]}px',
        "--font-size-3xl": f'{t["font_size_h2"]}px',
        "--font-size-4xl": f'{t["font_size_h1"]}px',
        "--font-size-6xl": f'{t["font_size_display"]}px',
        "--qorg-body-line-height": str(t["body_line_height"]),
        "--qorg-paragraph-line-height": str(t["paragraph_line_height"]),
        "--qorg-heading-line-height": str(t["heading_line_height"]),
    }
    if t.get("font_family"):
        values["--qorg-font-family"] = t["font_family"]
    return ";".join(f"{key}:{value}" for key, value in values.items())


def get_login_configuration():
    doc = frappe.get_single(SETTINGS)
    names = (
        "enable_login_experience", "show_login_language_switcher", "login_brand_logo",
        "login_footer_text", "login_form_title", "login_form_subtitle",
        "login_image_panel_width", "login_slide_interval", "login_return_label",
        "login_return_url",
    )
    config = {name: _value(doc, name) for name in names if doc.meta.has_field(name)}
    slides = []
    if doc.meta.has_field("login_slides"):
        for row in doc.get("login_slides") or []:
            if row.enabled and row.image:
                slides.append({
                    "image": row.image,
                    "mobile_image": row.mobile_image,
                    "title": row.title,
                    "subtitle": row.subtitle,
                    "image_position": row.image_position or "Center",
                    "overlay_opacity": max(0, min(100, int(row.overlay_opacity or 38))),
                    "text_alignment": row.text_alignment or "Center",
                })
    if not slides and doc.meta.has_field("login_background_image") and doc.login_background_image:
        slides.append({
            "image": doc.login_background_image,
            "mobile_image": None,
            "title": _value(doc, "login_visual_title"),
            "subtitle": _value(doc, "login_visual_subtitle"),
            "image_position": _value(doc, "login_background_position") or "Center",
            "overlay_opacity": 38,
            "text_alignment": "Center",
        })
    config["slides"] = slides[:6]
    config["ui_tokens"] = get_ui_tokens(getattr(frappe.local, "lang", None))
    config["font_stylesheet_url"] = get_font_stylesheet_url()
    return config

THEME_COLOR_PREFIXES = ("desk_light_", "desk_dark_", "web_light_", "web_dark_", "light_sidebar_", "dark_sidebar_", "light_menu_", "dark_menu_")
THEME_SIZE_FIELDS = (
    "default_field_radius", "default_button_radius", "default_card_radius", "default_menu_radius",
    "desk_field_radius", "desk_field_height", "desk_button_radius", "desk_button_height", "desk_card_radius",
    "web_field_radius", "web_field_height", "web_button_radius", "web_button_height", "web_card_radius",
    "sidebar_item_height", "sidebar_item_radius", "sidebar_item_padding", "menu_radius", "menu_item_height",
    "menu_item_radius", "menu_item_padding",
)


def get_theme_configuration():
    doc = frappe.get_single(SETTINGS)
    colors = {}
    sizes = {}
    for field in doc.meta.fields:
        name = field.fieldname
        if field.fieldtype == "Color" and name.startswith(THEME_COLOR_PREFIXES):
            value = str(doc.get(name) or field.default or "").strip()
            if HEX_RE.fullmatch(value):
                colors[name] = value.upper()
        elif name in THEME_SIZE_FIELDS:
            try:
                sizes[name] = int(doc.get(name) or field.default or 0)
            except (TypeError, ValueError):
                sizes[name] = 0
    return {
        "colors": colors,
        "sizes": sizes,
        "primary_color": _color(doc, "primary_color"),
        "secondary_color": _color(doc, "secondary_color"),
    }
