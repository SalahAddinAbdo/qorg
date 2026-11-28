# Learning and Performance Architecture Rules

This document records the source-level architecture contract for the Employee Lifecycle learning and performance capability.

- Never replace the complete field order of a standard DocType. Add or position only the managed fields owned by QOrg.
- Python domain services own validation, calculations, state transitions, and permission-sensitive business rules.
- Client scripts provide user guidance and convenience only; they must not be the authoritative control layer.
- Provisioning must be additive, idempotent, and safe to execute during install and repeated migrations.
- Standard Frappe HR and ERPNext records remain authoritative wherever a standard capability exists.
- Audit routines are read-only unless an explicit repair action is requested and recorded.
