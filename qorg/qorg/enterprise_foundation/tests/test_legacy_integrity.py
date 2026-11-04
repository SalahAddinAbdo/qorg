from __future__ import annotations

import ast
import json
from pathlib import Path

import frappe
from frappe.tests.utils import FrappeTestCase


class TestLegacyIntegrity(FrappeTestCase):
    def test_no_operational_qfap_imports(self):
        package_root = Path(frappe.get_app_path("qorg", "qorg"))
        offenders = []
        for path in package_root.rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    if any(alias.name == "qfap_adds" or alias.name.startswith("qfap_adds.") for alias in node.names):
                        offenders.append(f"{path}:{node.lineno}")
                elif isinstance(node, ast.ImportFrom):
                    if node.module and (node.module == "qfap_adds" or node.module.startswith("qfap_adds.")):
                        offenders.append(f"{path}:{node.lineno}")
        self.assertEqual(offenders, [])

    def test_workflow_sample_uses_current_responsibility_routing(self):
        path = Path(frappe.get_app_path("qorg", "reference_sources", "Workflow Sample.json"))
        payload = json.loads(path.read_text(encoding="utf-8"))
        transitions = payload.get("transitions") or []
        self.assertTrue(transitions)
        allowed = {
            "Keep Current Responsible",
            "Select Next User",
            "Return to Previous Responsible",
            "Return to Document Creator",
            "Clear Responsibility",
        }
        for row in transitions:
            self.assertNotIn("custom_assignment_required", row)
            self.assertNotIn("custom_target_user_field", row)
            self.assertIn(row.get("custom_responsibility_routing"), allowed)
