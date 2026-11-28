# Payroll and Workforce Allocation v3.0.2 - Deployment

## Scope
Deploy the QOrg payroll and workforce allocation capability through the Git repository only. Do not patch application files directly on the server.

## Preconditions
- Supported runtime: Frappe, ERPNext, and HRMS version 16.
- Clean QOrg Git worktree and a verified site backup with files.
- All payroll source tests pass with `allow_tests` returned to `false`.
- Capability audit reports `blockers = []` and `ready_for_pilot = True`.

## Deployment sequence
1. Update the QOrg checkout from the approved Git branch.
2. Run `bench --site <site> backup --with-files --compress`.
3. Run `bench --site <site> migrate`.
4. Run `bench build --app qorg`, clear cache, and restart Bench services.
5. Run the provisioning entry point twice to prove repeatability:
   `qorg.qorg.payroll_workforce_allocation.provisioning.provision_payroll_workforce_allocation`.
6. Run the daily task once:
   `qorg.qorg.payroll_workforce_allocation.scheduled_tasks.daily`.
7. Run runtime validation, the capability audit, controller checks, hook checks, and `run_acceptance()`.
8. Capture an idempotency snapshot, run a second migrate, capture the second snapshot, and compare stable metadata.
9. Confirm web and worker services are RUNNING and the Git worktree is clean.

## Technical acceptance
- Runtime issues: `[]`.
- Metadata passed: `True`.
- Runtime passed: `True`.
- Capability blockers: `[]`.
- Ready-for-pilot indicator: `True`.
- All payroll test modules pass.
- No duplicate Custom Fields, roles, reports, Print Formats, Notifications, Workspaces, or permissions after the second provisioning/migrate cycle.

Operational accounting, budget, liability, payment reconciliation, privacy, report, print, fresh-install, and upgrade gates remain evidence-based acceptance items and must not be marked passed without their recorded scenarios.
