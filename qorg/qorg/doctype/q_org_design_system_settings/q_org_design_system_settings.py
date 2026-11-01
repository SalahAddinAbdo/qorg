import re
from urllib.parse import urlparse

import frappe
from frappe import _
from frappe.model.document import Document

HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")


class QOrgDesignSystemSettings(Document):
    def validate(self):
        self._validate_colors()
        self._validate_shape()
        self._validate_typography()
        self._validate_font_source()
        self._validate_login_slides()

    def _validate_colors(self):
        fields = (
            "primary_color", "secondary_color", "page_background_color", "surface_color",
            "control_background_color", "primary_text_color", "muted_text_color", "border_color",
        )
        for fieldname in fields:
            if self.meta.has_field(fieldname) and not HEX_RE.fullmatch(str(self.get(fieldname) or "").strip()):
                frappe.throw(_("{0} must use #RRGGBB format.").format(self.meta.get_label(fieldname)))

    def _validate_shape(self):
        for fieldname, maximum in (("border_radius", 32), ("large_border_radius", 48)):
            if self.meta.has_field(fieldname):
                value = int(self.get(fieldname) or 0)
                if not 0 <= value <= maximum:
                    frappe.throw(_("{0} must be between 0 and {1} pixels.").format(self.meta.get_label(fieldname), maximum))

    def _validate_typography(self):
        ordered = [
            "font_size_xs", "font_size_sm", "font_size_base", "font_size_h6", "font_size_lg",
            "font_size_h5", "font_size_h4", "font_size_h3", "font_size_h2", "font_size_h1",
            "font_size_display",
        ]
        values = []
        for fieldname in ordered:
            if self.meta.has_field(fieldname):
                value = int(self.get(fieldname) or 0)
                if not 10 <= value <= 96:
                    frappe.throw(_("{0} must be between 10 and 96 pixels.").format(self.meta.get_label(fieldname)))
                values.append((fieldname, value))
        for previous, current in zip(values, values[1:]):
            if current[1] < previous[1]:
                frappe.throw(_("Typography sizes must be ascending. {0} cannot be smaller than {1}.").format(
                    self.meta.get_label(current[0]), self.meta.get_label(previous[0])))
        for fieldname in ("body_line_height", "paragraph_line_height", "heading_line_height"):
            if self.meta.has_field(fieldname):
                value = float(self.get(fieldname) or 0)
                if not 1.0 <= value <= 2.0:
                    frappe.throw(_("{0} must be between 1.0 and 2.0.").format(self.meta.get_label(fieldname)))

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
