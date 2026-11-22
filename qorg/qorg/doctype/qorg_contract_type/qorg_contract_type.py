import frappe
from frappe import _
from frappe.model.document import Document

STANDARD_PARTIES = {"Customer", "Supplier", "Employee"}

class QOrgContractType(Document):
    def validate(self):
        self._validate_party_policy()
        self._validate_requirements()

    def _validate_party_policy(self):
        rows = [row for row in self.allowed_parties if row.is_active]
        if self.party_model == "No Counterparty":
            if rows:
                frappe.throw(_("No Counterparty types cannot define allowed parties."))
            self.default_party_type = None
            self.default_extended_party_doctype = None
            self.require_primary_party = 0
            self.allow_multiple_parties = 0
            return
        if not rows:
            frappe.throw(_("At least one active allowed party is required."))
        seen = set()
        defaults = []
        for row in rows:
            key = (row.party_mode, row.party_doctype)
            if key in seen:
                frappe.throw(_("Duplicate allowed party: {0} ({1}).").format(row.party_doctype, row.party_mode))
            seen.add(key)
            if not frappe.db.exists("DocType", row.party_doctype):
                frappe.throw(_("Party DocType {0} does not exist.").format(row.party_doctype))
            if row.party_mode == "Standard" and row.party_doctype not in STANDARD_PARTIES:
                frappe.throw(_("Standard party must be Customer, Supplier, or Employee."))
            if row.party_mode == "Extended" and row.party_doctype in STANDARD_PARTIES:
                frappe.throw(_("Use Standard mode for {0}.").format(row.party_doctype))
            if row.is_default:
                defaults.append(row)
        if len(defaults) > 1:
            frappe.throw(_("Only one allowed party can be the default."))
        if self.party_model == "Standard Party" and any(r.party_mode != "Standard" for r in rows):
            frappe.throw(_("Standard Party types can only contain Standard allowed parties."))
        if self.party_model == "Extended Party" and any(r.party_mode != "Extended" for r in rows):
            frappe.throw(_("Extended Party types can only contain Extended allowed parties."))
        self.allow_multiple_parties = 1 if self.party_model == "Multiple Parties" else 0
        if defaults:
            default = defaults[0]
            self.default_party_type = default.party_doctype if default.party_mode == "Standard" else None
            self.default_extended_party_doctype = default.party_doctype if default.party_mode == "Extended" else None

    def _validate_requirements(self):
        if self.requires_value and self.allows_zero_value:
            frappe.throw(_("A type that requires a contract value cannot allow zero-value contracts."))
        if self.requires_budget_line:
            self.requires_funding_context = 1
        if self.requires_award_decision:
            self.requires_procurement_source = 1
        if self.category == "Employment":
            self.requires_employee = 1
        if self.category in {"Volunteer", "Internship"}:
            self.requires_external_person = 1
