# Payroll and Workforce Allocation v3.0.2 - Rollback

## Trigger conditions
Rollback when deployment introduces a migration traceback, runtime blocker, metadata incompatibility, duplicate provisioning artifacts, posting imbalance, or an unrecoverable service failure.

## Procedure
1. Stop user activity and preserve logs and the generated acceptance JSON files.
2. Record the deployed Git commit and `git status --short`.
3. Restore the verified pre-deployment database and files backup using the standard Bench restore procedure.
4. Check out the previously approved QOrg commit. Do not edit application files on the server.
5. Run migrate, build QOrg assets, clear cache, and restart services.
6. Re-run runtime compatibility and the capability audit.
7. Confirm web and worker services are RUNNING and reconcile any external payroll or accounting transaction created after the backup boundary.

## Data warning
Do not use source rollback alone after payroll, Journal Entry, Payment Entry, or GL transactions have been posted. Restore or reverse business transactions through controlled ERPNext documents and retain the audit trail.

## Rollback evidence
Retain the backup identifier, old and new Git commits, timestamps, runtime output, capability audit, service status, and the decision owner.
