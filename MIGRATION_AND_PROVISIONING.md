# QOrg Migration and Provisioning Policy

## Purpose

This policy defines where QOrg lifecycle changes belong and prevents migrations, provisioning, and runtime repair from overlapping.

## Mechanisms

### `patches.txt`
Use for a one-time, ordered data or schema transition that must be recorded in Frappe Patch Log. A patch must be importable, deterministic, restart-safe, and safe when the previous attempt completed only partially.

### `after_install`
Use to create the managed baseline required on a clean site. Every function must adopt an existing compatible record, create a missing record, and avoid overwriting user-managed values without an explicit managed-state rule.

### `after_migrate`
Use for repeatable reconciliation that must run after every schema migration. Functions registered here must be idempotent. Do not place irreversible one-time data conversions here unless the function has its own durable completion marker.

### Module `provisioning.py`
Use for managed records such as Custom Fields, Property Setters, Workflows, Notifications, Web Forms, Reports, Roles, and settings defaults. Provisioners must compare before writing and must preserve compatible manual configuration where QOrg does not own the value.

### Module `migration.py`
Use for legacy adoption, field-to-field migration, ownership reconciliation, and versioned transitions. Prefer calling versioned one-time migrations from `patches.txt`. If a migration remains in `after_migrate`, it must be demonstrably idempotent and documented.

### Reconciliation and audit
Use for detecting or safely repairing operational inconsistencies after source documents exist. Reconciliation may not fabricate accounting entries or silently modify submitted financial documents. Corrections must use standard cancellation, amendment, reversal, or journal processes.

## Required deployment sequence

1. Take a complete database and files backup.
2. Deploy the QOrg source.
3. Run `bench --site SITE migrate`.
4. Run `bench build --app qorg`.
5. Clear cache and website cache.
6. Restart services.
7. Run module audits and server tests.
8. Run `migrate` a second time in staging and compare managed configuration.
9. Complete functional acceptance for every changed cycle.

## Ownership rules

- QOrg Standard DocTypes use `custom = 0` and module `QOrg`.
- QOrg fields on standard DocTypes remain Custom Fields marked as system-generated and owned by module `QOrg`.
- QOrg adopts compatible existing records and must not delete unrelated customization.
- Legacy `qfap_adds` references may remain only inside explicit migration, compatibility, or integrity-test code until migration closure.

## Release gate

A change is ready for production only when static validation, import validation, migration, idempotency, affected-cycle server tests, and rollback or reversal behavior have passed on staging.
