from __future__ import annotations

import importlib
import importlib.util
from pathlib import Path


LIST_HOOKS = (
    "app_include_js", "app_include_css", "web_include_js", "web_include_css",
    "before_migrate", "after_install", "after_migrate",
)


def _assert_unique(values, hook_name):
    duplicates = sorted({value for value in values if values.count(value) > 1})
    assert not duplicates, f"Duplicate values in {hook_name}: {duplicates}"


def test_hook_lists_have_no_duplicates():
    hooks = importlib.import_module("qorg.hooks")
    for hook_name in LIST_HOOKS:
        _assert_unique(list(getattr(hooks, hook_name, [])), hook_name)


def test_registered_python_handlers_resolve():
    hooks = importlib.import_module("qorg.hooks")
    dotted_paths = []
    dotted_paths.extend(hooks.before_migrate)
    dotted_paths.extend(hooks.after_install)
    dotted_paths.extend(hooks.after_migrate)
    for events in hooks.doc_events.values():
        for handlers in events.values():
            dotted_paths.extend(handlers if isinstance(handlers, list) else [handlers])
    dotted_paths.extend(hooks.permission_query_conditions.values())
    dotted_paths.extend(hooks.has_permission.values())
    for path in dotted_paths:
        module_name, attribute = path.rsplit(".", 1)
        module = importlib.import_module(module_name)
        assert hasattr(module, attribute), path


def test_registered_qorg_assets_exist():
    hooks = importlib.import_module("qorg.hooks")
    app_root = Path(importlib.util.find_spec("qorg").origin).parent
    assets = []
    for hook_name in ("app_include_js", "app_include_css", "web_include_js", "web_include_css"):
        assets.extend(getattr(hooks, hook_name, []))
    for asset in assets:
        if not asset.startswith("/assets/qorg/"):
            continue
        relative = asset.removeprefix("/assets/qorg/")
        assert (app_root / "public" / relative).exists(), asset
