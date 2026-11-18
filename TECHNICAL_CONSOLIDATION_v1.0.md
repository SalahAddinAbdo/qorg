# QOrg Technical Consolidation v1.0

Source baseline: `qorg-main21`

## Completed

- Reorganized `qorg/hooks.py` into declarative sections without changing final hook values or registration order.
- Retained the approved application title and publisher as `QOrg`.
- Updated the application description to reflect the current enterprise scope.
- Replaced the obsolete Enhanced General Ledger-only README with the current application scope, installation, upgrade, and validation guidance.
- Added `MIGRATION_AND_PROVISIONING.md` to define Patch Log, install, migrate, provisioning, migration, and reconciliation responsibilities.
- Added `.gitignore` controls for Python cache, build, editor, log, and local environment artifacts.
- Removed `.pyc` and `__pycache__` entries from the packaged source.
- Added a hook integrity test that checks duplicate registrations and referenced QOrg assets/modules.

## Intentionally unchanged

- `qorg/patches.txt` order and content. No existing migration was moved between lifecycle mechanisms in this low-risk consolidation.
- DocTypes, reports, workflows, permissions, database logic, and runtime business rules.
- Existing install, migrate, and scheduled-task registration order.

## Required staging acceptance

```bash
bench --site YOUR-SITE backup --with-files
bench --site YOUR-SITE migrate
bench build --app qorg
bench --site YOUR-SITE clear-cache
bench --site YOUR-SITE clear-website-cache
bench restart
bench --site YOUR-SITE migrate
```

Then confirm Desk startup, portal routes, scheduler, Funding Agreement, Budget Line, Material Request, Purchase Receipt, Project, Task, External Opportunity, and the main workspaces.
