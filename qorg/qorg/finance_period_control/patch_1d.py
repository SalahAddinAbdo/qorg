from qorg.qorg.finance_period_control.legacy_migration import execute as migrate

def execute():
    migrate(dry_run=False)
