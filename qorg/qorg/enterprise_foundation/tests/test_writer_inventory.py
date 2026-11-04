from __future__ import annotations

import ast
import inspect
from pathlib import Path

import frappe
from frappe.tests.utils import FrappeTestCase

from qorg.qorg.enterprise_foundation import (
    interface_policy_engine,
    model_policy_engine,
    workflow_manager,
)


class TestManagedStateWriterInventory(FrappeTestCase):
    EXPECTED_WRITERS = {
        "enterprise_foundation/interface_policy_engine.py",
        "enterprise_foundation/model_policy_engine.py",
        "enterprise_foundation/workflow_manager.py",
    }

    @staticmethod
    def _is_managed_state_literal(node):
        return isinstance(node, ast.Constant) and node.value == "Managed Configuration State"

    def _has_document_api_write(self, path):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                continue
            if node.func.attr not in {"new_doc", "delete_doc"} or not node.args:
                continue
            if self._is_managed_state_literal(node.args[0]):
                return True
        return False

    def test_all_production_document_api_writers_are_known_and_guarded(self):
        package_root = Path(frappe.get_app_path("qorg", "qorg"))
        writers = set()
        for path in package_root.rglob("*.py"):
            relative = path.relative_to(package_root)
            if "tests" in relative.parts or path.name.startswith("test_"):
                continue
            if self._has_document_api_write(path):
                writers.add(relative.as_posix())
                source = path.read_text(encoding="utf-8")
                self.assertIn("managed_state_write", source, path.as_posix())
                self.assertIn("with managed_state_write():", source, path.as_posix())
        self.assertEqual(writers, self.EXPECTED_WRITERS)

    def test_known_writer_functions_use_internal_context(self):
        self.assertIn("with managed_state_write():", inspect.getsource(model_policy_engine._save))
        self.assertIn("with managed_state_write():", inspect.getsource(interface_policy_engine._save_state))
        self.assertIn("with managed_state_write():", inspect.getsource(workflow_manager._save_state))
