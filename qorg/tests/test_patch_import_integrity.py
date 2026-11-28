from __future__ import annotations

import importlib
from pathlib import Path
import unittest

import frappe


class TestPatchImportIntegrity(unittest.TestCase):
    def test_all_active_patch_modules_import(self):
        patch_file = Path(frappe.get_app_path("qorg", "patches.txt"))
        failures = []

        for raw_line in patch_file.read_text(encoding="utf-8").splitlines():
            dotted_path = raw_line.strip()
            if (
                not dotted_path
                or dotted_path.startswith("#")
                or dotted_path.startswith("[")
            ):
                continue

            try:
                importlib.import_module(dotted_path)
            except Exception as exc:  # pragma: no cover - details are asserted below
                failures.append(f"{dotted_path}: {exc!r}")

        self.assertEqual([], failures, "Broken patch imports:\n" + "\n".join(failures))
