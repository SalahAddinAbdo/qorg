from unittest.mock import patch
from frappe.tests.utils import FrappeTestCase
from qorg.qorg.finance_period_control.legacy_migration import execute
class TestLegacyMigration(FrappeTestCase):
    @patch("qorg.qorg.finance_period_control.legacy_migration.frappe.get_all")
    def test_empty_database_is_idempotent(self, get_all):
        get_all.return_value=[]
        self.assertEqual(execute(dry_run=True),{"periods_created":0,"lines_migrated":0,"review_required":0,"skipped":0})
