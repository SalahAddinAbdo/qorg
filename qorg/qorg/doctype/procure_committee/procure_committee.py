import frappe
from frappe import _
from frappe.model.document import Document
from qorg.qorg.procurement_contracting.doctype_validators import validate_committee

class ProcureCommittee(Document):
    def validate(self):
        validate_committee(self)
        active=[row for row in self.members if row.active and not row.recused]
        if not active:
            frappe.throw(_("At least one active, non-recused committee member is required."))
        users=[row.user for row in self.members]
        if len(users)!=len(set(users)):
            frappe.throw(_("The same user cannot be added to the committee more than once."))
        chairs=[row for row in active if row.committee_role=="Chair"]
        if len(chairs)!=1:
            frappe.throw(_("Exactly one active, non-recused Chair is required."))
        voters=[row for row in active if row.voting_member]
        if self.quorum and self.quorum>len(voters):
            frappe.throw(_("Quorum cannot exceed the number of active voting members."))
        weights=[float(row.member_weight or 0) for row in voters]
        if any(weights) and round(sum(weights),6)!=100:
            frappe.throw(_("Voting member weights must total exactly 100%. Current total: {0}%.").format(sum(weights)))
