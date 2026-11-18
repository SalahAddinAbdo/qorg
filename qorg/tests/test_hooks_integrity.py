from __future__ import annotations

import importlib
import importlib.util
import unittest
from pathlib import Path


LIST_HOOKS = (
    "app_include_js",
    "app_include_css",
    "web_include_js",
    "web_include_css",
    "before_migrate",
    "after_install",
    "after_migrate",
)


class TestHooksIntegrity(unittest.TestCase):
    def setUp(self):
        self.hooks = importlib.import_module("qorg.hooks")

    def test_hook_lists_have_no_duplicates(self):
        for hook_name in LIST_HOOKS:
            values = list(getattr(self.hooks, hook_name, []))
            duplicates = sorted({value for value in values if values.count(value) > 1})
            self.assertFalse(
                duplicates,
                f"Duplicate values in {hook_name}: {duplicates}",
            )

    def test_registered_python_handlers_resolve(self):
        dotted_paths = []
        dotted_paths.extend(self.hooks.before_migrate)
        dotted_paths.extend(self.hooks.after_install)
        dotted_paths.extend(self.hooks.after_migrate)

        for events in self.hooks.doc_events.values():
            for handlers in events.values():
                dotted_paths.extend(handlers if isinstance(handlers, list) else [handlers])

        dotted_paths.extend(self.hooks.permission_query_conditions.values())
        dotted_paths.extend(self.hooks.has_permission.values())

        for path in sorted(set(dotted_paths)):
            module_name, attribute = path.rsplit(".", 1)
            module = importlib.import_module(module_name)
            self.assertTrue(
                hasattr(module, attribute),
                f"Registered hook handler does not resolve: {path}",
            )

    def test_registered_qorg_assets_exist(self):
        app_spec = importlib.util.find_spec("qorg")
        self.assertIsNotNone(app_spec, "The qorg Python package could not be resolved.")
        self.assertIsNotNone(app_spec.origin, "The qorg package has no origin path.")
        app_root = Path(app_spec.origin).parent

        assets = []
        for hook_name in (
            "app_include_js",
            "app_include_css",
            "web_include_js",
            "web_include_css",
        ):
            assets.extend(getattr(self.hooks, hook_name, []))

        for asset in assets:
            if not asset.startswith("/assets/qorg/"):
                continue
            relative_path = asset.removeprefix("/assets/qorg/")
            asset_path = app_root / "public" / relative_path
            self.assertTrue(
                asset_path.exists(),
                f"Registered QOrg asset does not exist: {asset} -> {asset_path}",
            )
