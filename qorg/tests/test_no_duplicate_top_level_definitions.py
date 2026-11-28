"""Source integrity guard against shadowed top-level definitions."""
import ast
import unittest
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[1]


class TestNoDuplicateTopLevelDefinitions(unittest.TestCase):
    def test_no_duplicate_top_level_definitions(self):
        duplicates = []
        for path in sorted(APP_ROOT.rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            seen = {}
            for node in tree.body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    if node.name in seen:
                        duplicates.append({
                            "file": str(path.relative_to(APP_ROOT)),
                            "name": node.name,
                            "first_line": seen[node.name],
                            "second_line": node.lineno,
                        })
                    else:
                        seen[node.name] = node.lineno
        self.assertEqual(duplicates, [], f"Duplicate top-level definitions: {duplicates}")
