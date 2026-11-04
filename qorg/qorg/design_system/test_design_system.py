from __future__ import annotations

import unittest

from qorg.qorg.design_system.service import DEFAULTS, HEX_RE, tokens_to_css


class TestDesignSystem(unittest.TestCase):
    def _tokens(self):
        tokens = dict(DEFAULTS)
        tokens["font_family"] = "Inter, sans-serif"
        tokens["font_weights"] = [400, 500, 600, 700]
        return tokens

    def test_default_colors_are_valid_six_digit_hex_values(self):
        color_fields = (
            "primary_color",
            "secondary_color",
            "page_background_color",
            "surface_color",
            "control_background_color",
            "primary_text_color",
            "muted_text_color",
            "border_color",
        )
        for fieldname in color_fields:
            with self.subTest(fieldname=fieldname):
                self.assertIsNotNone(HEX_RE.fullmatch(DEFAULTS[fieldname]))

    def test_tokens_to_css_uses_current_service_contract(self):
        css = tokens_to_css(self._tokens())
        self.assertIn(f'--primary-color:{DEFAULTS["primary_color"]}', css)
        self.assertIn(f'--qorg-secondary-color:{DEFAULTS["secondary_color"]}', css)
        self.assertIn(f'--border-radius:{DEFAULTS["border_radius"]}px', css)
        self.assertIn("--qorg-font-family:Inter, sans-serif", css)

    def test_tokens_to_css_is_stable_for_same_input(self):
        tokens = self._tokens()
        self.assertEqual(tokens_to_css(tokens), tokens_to_css(dict(tokens)))
