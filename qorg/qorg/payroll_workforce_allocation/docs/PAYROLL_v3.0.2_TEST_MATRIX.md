# Payroll and Workforce Allocation v3.0.2 - Test Matrix

| Area | Required evidence | Pass criterion |
|---|---|---|
| Source integrity | All payroll `test_*.py` modules | No failures or errors |
| Controllers and Meta | Eleven payroll DocTypes and child tables | Controllers load; expected child records have `istable = 1` |
| Hooks | Migration, scheduler, Payroll Entry, Salary Slip, Payment Entry, permissions, and client scripts | Every required hook resolves |
| Provisioning | Two consecutive executions | No traceback, duplicates, or destructive changes |
| Scheduler | Manual daily-task execution | No traceback or unjustified state changes |
| Runtime compatibility | `validate_runtime` | Empty issue list |
| Capability audit | `run_payroll_capability_audit` | No blockers; ready-for-pilot is true |
| Migration | Two consecutive site migrations | Both succeed |
| Idempotency | Before/after snapshots | Stable metadata and no duplicate artifacts |
| Accounting | Allocation posting and reversal scenarios | Balanced entries and successful reversal |
| Budget control | Eligible, ineligible, partial, and over-budget scenarios | Policy outcomes and no double count |
| Liabilities | Configured split modes and reconciliation | Correct dimensions, totals, and status |
| Payments | Linked and partial payment scenarios | Correct reconciliation without duplicate allocation |
| Permissions/privacy | Payroll, accounts, grants, audit, and unauthorized users | Least privilege and disclosure controls enforced |
| Reports/print | Six payroll reports and authorized print disclosure | Correct totals, filters, columns, and access |
| Fresh install/upgrade | Empty site and representative prior release | Successful install/upgrade without metadata drift |
| Services and Git | Supervisor status and repository checks | Services RUNNING; worktree clean; `git diff --check` clean |

Acceptance evidence must be recorded in the runtime acceptance JSON. A default `False` gate means that the operational scenario has not yet been evidenced, not automatically that the source is defective.
