import re
from urllib.parse import urlparse

import frappe
from frappe import _
from frappe.model.document import Document

HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")


class QOrgDesignSystemSettings(Document):
    def validate(self):
        self._validate_colors()
        self._validate_dimensions()
        self._validate_typography()
        self._validate_font_source()
        self._validate_login_slides()

    def _validate_colors(self):
        for field in self.meta.fields:
            if field.fieldtype != "Color" or not self.get(field.fieldname):
                continue
            if not HEX_RE.fullmatch(str(self.get(field.fieldname)).strip()):
                frappe.throw(_("{0} must use #RRGGBB format.").format(field.label or field.fieldname))

    def _validate_dimensions(self):
        height_fields = {"desk_field_height", "desk_button_height", "web_field_height", "web_button_height", "sidebar_item_height", "menu_item_height"}
        padding_fields = {"sidebar_item_padding", "menu_item_padding"}
        for field in self.meta.fields:
            name = field.fieldname
            if field.fieldtype != "Int" or self.get(name) in (None, ""):
                continue
            value = int(self.get(name) or 0)
            if name in height_fields and not 24 <= value <= 64:
                frappe.throw(_("{0} must be between 24 and 64 pixels.").format(field.label))
            if "radius" in name and not 0 <= value <= 48:
                frappe.throw(_("{0} must be between 0 and 48 pixels.").format(field.label))
            if name in padding_fields and not 0 <= value <= 32:
                frappe.throw(_("{0} must be between 0 and 32 pixels.").format(field.label))
            if name == "workspace_widget_hover_lift" and not 0 <= value <= 8:
                frappe.throw(_("{0} must be between 0 and 8 pixels.").format(field.label))

    def _validate_typography(self):
        ordered = ["font_size_xs", "font_size_sm", "font_size_base", "font_size_h6", "font_size_lg", "font_size_h5", "font_size_h4", "font_size_h3", "font_size_h2", "font_size_h1", "font_size_display"]
        values = [(name, int(self.get(name) or 0)) for name in ordered if self.meta.has_field(name)]
        for name, value in values:
            if not 10 <= value <= 96:
                frappe.throw(_("{0} must be between 10 and 96 pixels.").format(self.meta.get_label(name)))
        for previous, current in zip(values, values[1:]):
            if current[1] < previous[1]:
                frappe.throw(_("Typography sizes must be ascending. {0} cannot be smaller than {1}.").format(self.meta.get_label(current[0]), self.meta.get_label(previous[0])))
        for name in ("body_line_height", "paragraph_line_height", "heading_line_height"):
            if self.meta.has_field(name) and not 1.0 <= float(self.get(name) or 0) <= 2.0:
                frappe.throw(_("{0} must be between 1.0 and 2.0.").format(self.meta.get_label(name)))

    def _validate_font_source(self):
        if not self.meta.has_field("font_source"):
            return
        source = self.font_source or "Frappe Default"
        url = str(self.font_stylesheet_url or "").strip()
        if source in ("Google Fonts", "Custom Web Font"):
            if not url:
                frappe.throw(_("Font Stylesheet URL is required for the selected font source."))
            parsed = urlparse(url)
            if parsed.scheme != "https":
                frappe.throw(_("Font Stylesheet URL must use HTTPS."))
            if source == "Google Fonts" and parsed.netloc not in ("fonts.googleapis.com", "fonts.gstatic.com"):
                frappe.throw(_("Google Fonts must use the official fonts.googleapis.com URL."))

    def _validate_login_slides(self):
        if self.meta.has_field("login_slides") and len(self.login_slides or []) > 6:
            frappe.throw(_("A maximum of six login slides is allowed."))
        if self.meta.has_field("login_image_panel_width") and not 35 <= int(self.login_image_panel_width or 48) <= 60:
            frappe.throw(_("Image Panel Width must be between 35% and 60%."))
        if self.meta.has_field("login_slide_interval") and not 3 <= int(self.login_slide_interval or 6) <= 30:
            frappe.throw(_("Slide Interval must be between 3 and 30 seconds."))
