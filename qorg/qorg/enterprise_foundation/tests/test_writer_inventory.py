from __future__ import annotations

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

    def test_all_document_api_writers_are_known_and_guarded(self):
        package_root = Path(frappe.get_app_path("qorg", "qorg"))
        writers = set()
        for path in package_root.rglob("*.py"):
            source = path.read_text(encoding="utf-8", errors="ignore")
            if "Managed Configuration State" not in source:
                continue
            if any(token in source for token in (
                'new_doc("Managed Configuration State")',
                'delete_doc("Managed Configuration State"',
            )):
                writers.add(path.relative_to(package_root).as_posix())
                self.assertIn("managed_state_write", source, path.as_posix())
                self.assertIn("with managed_state_write():", source, path.as_posix())
        self.assertEqual(writers, self.EXPECTED_WRITERS)

    def test_known_writer_functions_use_internal_context(self):
        self.assertIn("with managed_state_write():", inspect.getsource(model_policy_engine._save))
        self.assertIn("with managed_state_write():", inspect.getsource(interface_policy_engine._save_state))
        self.assertIn("with managed_state_write():", inspect.getsource(workflow_manager._save_state))
