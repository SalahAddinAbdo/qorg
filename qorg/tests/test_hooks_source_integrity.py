"""Source-only integrity checks for QOrg's declarative hook registry."""

from __future__ import annotations

import ast
import re
import unittest
from pathlib import Path


APP_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = APP_ROOT.parent
HOOKS_PATH = APP_ROOT / "hooks.py"
DOTTED_QORG_PATH = re.compile(r"qorg(?:\.[A-Za-z_][A-Za-z0-9_]*){2,}")


def _module_exists(dotted_path: str) -> bool:
    parts = dotted_path.split(".")
    for end in range(len(parts), 1, -1):
        candidate = REPOSITORY_ROOT.joinpath(*parts[:end])
        if candidate.with_suffix(".py").is_file() or (candidate / "__init__.py").is_file():
            return True
    return False


class TestHooksSourceIntegrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = HOOKS_PATH.read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.source, filename=str(HOOKS_PATH))

    def test_hooks_is_valid_declarative_python(self):
        assignments = [
            node
            for node in self.tree.body
            if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign))
        ]
        self.assertGreater(len(assignments), 20)

    def test_qorg_hook_modules_exist(self):
        unresolved = sorted(
            path
            for path in set(DOTTED_QORG_PATH.findall(self.source))
            if not _module_exists(path)
        )
        self.assertFalse(unresolved, f"Unresolved QOrg hook module paths: {unresolved}")

    def test_no_duplicate_top_level_literal_list_entries(self):
        duplicates = {}
        for node in self.tree.body:
            if not isinstance(node, ast.Assign) or len(node.targets) != 1:
                continue
            target = node.targets[0]
            if not isinstance(target, ast.Name) or not isinstance(node.value, (ast.List, ast.Tuple)):
                continue
            values = []
            for item in node.value.elts:
                try:
                    value = ast.literal_eval(item)
                except (ValueError, TypeError):
                    continue
                if isinstance(value, str):
                    values.append(value)
            repeated = sorted({value for value in values if values.count(value) > 1})
            if repeated:
                duplicates[target.id] = repeated
        self.assertFalse(duplicates, f"Duplicate top-level hook entries: {duplicates}")


if __name__ == "__main__":
    unittest.main()
