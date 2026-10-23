from __future__ import annotations

CONFIGURATION_VERSION = "1.1.2"
OPERATING_MODES = ("Standard Only", "Extensions", "Full Portal / Extended Cycle")
MODEL_POLICIES = ("Enabled", "Hidden from Navigation", "Restricted", "Read Only", "Feature Disabled", "Deprecated")

FEATURES = (
    ("external_people", "External People", "Full Portal / Extended Cycle"),
    ("public_opportunities", "Public Opportunities", "Full Portal / Extended Cycle"),
    ("volunteer_management", "Volunteer Management", "Extensions"),
    ("extended_recruitment", "Extended Recruitment", "Extensions"),
    ("mobile_attendance", "Mobile Attendance", "Extensions"),
    ("attendance_permissions", "Attendance Permissions", "Extensions"),
    ("extended_training", "Extended Training", "Extensions"),
    ("multi_source_appraisal", "Multi-Source Appraisal", "Extensions"),
    ("extended_procurement", "Extended Procurement", "Extensions"),
    ("procurement_portal", "Procurement Portal", "Full Portal / Extended Cycle"),
    ("supplier_communications", "Supplier Communications", "Extensions"),
    ("service_acceptance", "Service Acceptance", "Extensions"),
    ("non_procurement_disbursement", "Non-Procurement Disbursement", "Extensions"),
    ("recurring_services", "Recurring Services", "Extensions"),
    ("payroll_allocation", "Payroll Allocation", "Extensions"),
    ("asset_operations", "Asset Operations", "Extensions"),
    ("fleet_management", "Fleet Management", "Extensions"),
    ("accountability_feedback", "Accountability and Feedback", "Extensions"),
)

CRITICAL_DOCTYPES = frozenset({
    "DocType", "DocField", "User", "Role", "Role Permission for Page and Report",
    "Custom Field", "Property Setter", "Company", "Module Def", "Installed Applications",
    "Workflow", "Workflow State", "Workflow Action Master", "Communication", "File",
    "Account", "GL Entry", "Stock Ledger Entry", "Payment Ledger Entry",
})
