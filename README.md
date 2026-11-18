# QOrg

QOrg is an enterprise operations application for Frappe, ERPNext, and HRMS version 16. It extends the standard platforms with integrated operational cycles for humanitarian and nonprofit organizations while following **Standard First, Extend Second, Create Last**.

## Core scope

- Enterprise foundation, feature governance, managed configuration, workflow responsibility routing, signatures, printing, navigation, and accounting dimensions.
- External people, public opportunities, recruitment, volunteering, internships, and short-term participation.
- Projects, tasks, results, indicators, beneficiaries, risks, compliance, change control, and project closure.
- Procurement, supplier portal, tendering, contracts, commitments, inventory, assets, custody, incidents, and physical verification.
- Operational finance, donors, funding agreements, project funding sources, budget lines, budget transfers, commitments, multi-currency controls, reconciliation, and grant reporting.

## Requirements

- Frappe Framework 16
- ERPNext 16
- HRMS 16
- MariaDB or PostgreSQL as supported by the installed Frappe release
- Redis, Node.js, Yarn, and the remaining dependencies required by Frappe Bench

Use matching release families for Frappe, ERPNext, and HRMS. Validate upgrades on a staging site before applying them to production.

## Installation

```bash
cd ~/frappe-bench
bench get-app https://github.com/SalahAddinAbdo/qorg.git
bench --site YOUR-SITE install-app qorg
bench build --app qorg
bench --site YOUR-SITE migrate
bench --site YOUR-SITE clear-cache
bench --site YOUR-SITE clear-website-cache
bench restart
```

## Upgrade

Take a complete database and files backup before every upgrade.

```bash
cd ~/frappe-bench
bench --site YOUR-SITE backup --with-files
bench update --reset
bench --site YOUR-SITE migrate
bench build --app qorg
bench --site YOUR-SITE clear-cache
bench --site YOUR-SITE clear-website-cache
bench restart
```

Run a second migration on staging when validating idempotency:

```bash
bench --site YOUR-SITE migrate
```

## Architecture and lifecycle

- `qorg/hooks.py` contains the final declarative Frappe registrations.
- `qorg/patches.txt` contains one-time framework patches tracked by Frappe Patch Log.
- Module `provisioning.py` functions create or reconcile managed configuration and must remain idempotent.
- Module `migration.py` functions reconcile schema or legacy records and must remain safe when called more than once.
- Runtime reconciliation and audit functions report operational inconsistencies without replacing accounting source documents.

See [MIGRATION_AND_PROVISIONING.md](MIGRATION_AND_PROVISIONING.md) for the lifecycle rules and deployment gates.

## Validation baseline

Before production deployment, complete at minimum:

1. Python and JSON static validation.
2. Clean-site installation test.
3. Upgrade test from the current production baseline.
4. Two consecutive `migrate` runs without unintended changes.
5. Module-specific server tests.
6. Submit, Cancel, Amend, permission, reconciliation, and rollback tests for the affected cycle.
7. Desk, portal, RTL/LTR, mobile, print, email, and report acceptance for changed surfaces.

## License

GPL-3.0.
