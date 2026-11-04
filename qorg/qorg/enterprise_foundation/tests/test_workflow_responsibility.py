from __future__ import annotations

from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from qorg.qorg.workflow.actions import (
    PREVIOUS_RESPONSIBLE_FIELD,
    ROUTING_CLEAR,
    ROUTING_CREATOR,
    ROUTING_KEEP,
    ROUTING_PREVIOUS,
    ROUTING_SELECT,
    _prepare_assignment,
)
from qorg.qorg.workflow.permissions import RESPONSIBLE_FIELD, can_override_responsibility


class _Meta:
    def has_field(self, fieldname):
        return fieldname in {RESPONSIBLE_FIELD, PREVIOUS_RESPONSIBLE_FIELD}


class _Doc:
    def __init__(self, current="current@example.com", previous="previous@example.com", owner="owner@example.com"):
        self.meta = _Meta()
        self.owner = owner
        self.values = {
            RESPONSIBLE_FIELD: current,
            PREVIOUS_RESPONSIBLE_FIELD: previous,
        }

    def get(self, key):
        return self.values.get(key)

    def set(self, key, value):
        self.values[key] = value


class TestWorkflowResponsibilityRouting(FrappeTestCase):
    def setUp(self):
        frappe.set_user("Administrator")
        self.validator = patch("qorg.qorg.workflow.actions._validate_next_user")
        self.validator.start()

    def tearDown(self):
        self.validator.stop()
        frappe.set_user("Administrator")

    def _transition(self, routing):
        return {"custom_responsibility_routing": routing, "custom_target_role": ""}

    def test_all_supported_routing_modes(self):
        cases = (
            (ROUTING_KEEP, "", "current@example.com"),
            (ROUTING_SELECT, "next@example.com", "next@example.com"),
            (ROUTING_PREVIOUS, "", "previous@example.com"),
            (ROUTING_CREATOR, "", "owner@example.com"),
            (ROUTING_CLEAR, "", ""),
        )
        for routing, next_user, expected in cases:
            with self.subTest(routing=routing):
                doc = _Doc()
                result = _prepare_assignment(doc, self._transition(routing), next_user)
                self.assertEqual(result["next_user"], expected)
                self.assertEqual(doc.get(RESPONSIBLE_FIELD), expected)
                if expected != "current@example.com":
                    self.assertEqual(doc.get(PREVIOUS_RESPONSIBLE_FIELD), "Administrator")

    def test_select_requires_next_user(self):
        with self.assertRaises(frappe.ValidationError):
            _prepare_assignment(_Doc(), self._transition(ROUTING_SELECT), "")

    def test_previous_requires_previous_user(self):
        with self.assertRaises(frappe.ValidationError):
            _prepare_assignment(
                _Doc(previous=""),
                self._transition(ROUTING_PREVIOUS),
                "",
            )

    def test_automatic_routing_rejects_conflicting_next_user(self):
        with self.assertRaises(frappe.ValidationError):
            _prepare_assignment(
                _Doc(),
                self._transition(ROUTING_CREATOR),
                "other@example.com",
            )

    def test_administrator_can_override_responsibility(self):
        self.assertTrue(can_override_responsibility("Administrator"))
