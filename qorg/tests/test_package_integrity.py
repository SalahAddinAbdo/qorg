"""Static packaging and ownership checks (no database needed)."""
import json
import os
import unittest

APP_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # .../qorg/qorg


class TestPackageIntegrity(unittest.TestCase):
    def test_every_python_directory_is_a_package(self):
        missing = []
        for dirpath, dirnames, filenames in os.walk(APP_ROOT):
            rel = os.path.relpath(dirpath, APP_ROOT)
            if rel.split(os.sep)[0] in ("public", "www", "templates", "reference_sources") or "__pycache__" in dirpath:
                continue
            if any(f.endswith(".py") for f in filenames) and "__init__.py" not in filenames:
                missing.append(rel)
        self.assertEqual(missing, [], "find_packages() would omit: %s" % missing)

    def test_custom_field_fixtures_are_managed(self):
        with open(os.path.join(APP_ROOT, "fixtures", "custom_field.json"), encoding="utf-8") as fh:
            rows = json.load(fh)
        bad = [r.get("name") for r in rows if r.get("module") != "QOrg" or int(r.get("is_system_generated") or 0) != 1]
        self.assertEqual(bad, [])

    def test_no_legacy_module_name_in_code(self):
        offenders = []
        for dirpath, _d, filenames in os.walk(os.path.join(APP_ROOT, "qorg")):
            for f in filenames:
                if f.endswith(".py"):
                    path = os.path.join(dirpath, f)
                    with open(path, encoding="utf-8") as fh:
                        if '"module": "Q Org"' in fh.read():
                            offenders.append(path)
        self.assertEqual(offenders, [])
