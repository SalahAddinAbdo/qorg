from __future__ import annotations
import hashlib, json
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate, now

class ServiceAllowanceAccrual(Document):
    def validate(self):
        if getdate(self.period_end) < getdate(self.period_start):
            frappe.throw(_("Period End cannot be before Period Start."))
        self._calculate_and_validate_lines()
        self.source_hash = self.get_source_hash()

    def on_submit(self):
        self.db_set("operational_status", "Approved", update_modified=False)

    def on_cancel(self):
        if self.journal_entry and frappe.db.get_value("Journal Entry", self.journal_entry, "docstatus") == 1:
            frappe.throw(_("Cancel the posted Journal Entry through its approved reversal process before cancelling this accrual."))
        self.db_set("operational_status", "Reversed", update_modified=False)

    def _calculate_and_validate_lines(self):
        gross = deductions = net = 0
        seen=set()
        type_doc = frappe.get_cached_doc("Service and Allowance Type", self.accrual_type)
        for row in self.lines:
            if not row.include: continue
            party = row.external_person or row.supplier or row.employee
            key=(party,row.site,row.service_item,row.attendance_reference)
            if party and key in seen: frappe.throw(_("Possible duplicate entitlement at row {0}.").format(row.idx))
            seen.add(key)
            if type_doc.item_requirement == "Required" and not row.service_item: frappe.throw(_("Service Item is required at row {0}.").format(row.idx))
            if type_doc.require_external_person and not row.external_person: frappe.throw(_("External Person is required at row {0}.").format(row.idx))
            if type_doc.require_site and not row.site: frappe.throw(_("Site / Location is required at row {0}.").format(row.idx))
            if type_doc.require_supporting_document and not row.supporting_document: frappe.throw(_("Supporting Document is required at row {0}.").format(row.idx))
            if type_doc.require_agreement and not row.contract_or_agreement: frappe.throw(_("Contract / Agreement is required at row {0}.").format(row.idx))
            if type_doc.require_attendance and not row.attendance_reference: frappe.throw(_("Attendance Reference is required at row {0}.").format(row.idx))
            if type_doc.require_service_acceptance and not row.service_acceptance: frappe.throw(_("Service Acceptance is required at row {0}.").format(row.idx))
            if type_doc.require_project and row.allocation_treatment == "Direct" and not row.project: frappe.throw(_("Project is required at row {0}.").format(row.idx))
            if type_doc.require_budget_line and row.allocation_treatment == "Direct" and not row.budget_line: frappe.throw(_("Budget Line is required at row {0}.").format(row.idx))
            self._validate_party(row, type_doc)
            if type_doc.maximum_days and flt(row.number_of_days) > flt(type_doc.maximum_days): frappe.throw(_("Number of Days exceeds the allowed maximum at row {0}.").format(row.idx))
            if type_doc.maximum_rate and flt(row.daily_rate or row.period_rate or row.rate) > flt(type_doc.maximum_rate): frappe.throw(_("Rate exceeds the allowed maximum at row {0}.").format(row.idx))
            qty = flt(row.number_of_days) if type_doc.calculation_method == "Days x Daily Rate" else flt(row.quantity or 1)
            unit_rate = flt(row.daily_rate or row.rate) if type_doc.calculation_method == "Days x Daily Rate" else flt(row.rate)
            amount = flt(row.period_rate or row.rate) if type_doc.calculation_method == "Fixed Amount" else qty * unit_rate
            row.gross_amount=amount; row.net_payable=amount-flt(row.deduction)-flt(row.tax_withheld)
            if row.net_payable < 0: frappe.throw(_("Net Payable cannot be negative at row {0}.").format(row.idx))
            self._validate_distribution(row)
            gross += amount; deductions += flt(row.deduction)+flt(row.tax_withheld); net += row.net_payable
        self.total_gross_amount=gross;self.total_deductions=deductions;self.total_net_payable=net

    def _validate_party(self, row, type_doc):
        selected=[x for x in (row.external_person,row.supplier,row.employee,row.volunteer_profile) if x]
        if len(selected) != 1: frappe.throw(_("Exactly one payee must be selected at row {0}.").format(row.idx))
        if row.external_person:
            person=frappe.db.get_value("External Person",row.external_person,["person_status","merged_into","identity_verification_status","payment_details_verified"],as_dict=True) or {}
            if person.get("person_status") != "Active" or person.get("merged_into"): frappe.throw(_("External Person must be active and not merged at row {0}.").format(row.idx))
            if type_doc.require_identity_verification and person.get("identity_verification_status") != "Verified": frappe.throw(_("Verified identity is required at row {0}.").format(row.idx))
            if type_doc.require_payment_verification and not person.get("payment_details_verified"): frappe.throw(_("Verified payment details are required at row {0}.").format(row.idx))

    def _validate_distribution(self,row):
        if row.allocation_treatment == "Direct" and not row.project: frappe.throw(_("Project is required for Direct allocation at row {0}.").format(row.idx))
        if row.project and frappe.db.get_value("Project",row.project,"company") != self.company: frappe.throw(_("Project does not belong to the selected Company at row {0}.").format(row.idx))
        if row.cost_center and frappe.db.get_value("Cost Center",row.cost_center,"company") != self.company: frappe.throw(_("Cost Center does not belong to the selected Company at row {0}.").format(row.idx))
        if row.budget_line and frappe.db.get_value("Budget Line",row.budget_line,"project") != row.project: frappe.throw(_("Budget Line does not belong to the selected Project at row {0}.").format(row.idx))
        if row.allocation_treatment == "Split Distribution":
            if not [x for x in self.cost_distributions if x.source_row == row.name]: frappe.throw(_("Cost Distribution is required at row {0}.").format(row.idx))
            seen=set()
            for x in [x for x in self.cost_distributions if x.source_row == row.name]:
                key=(x.project,x.cost_center,x.budget_line,x.funding_agreement,x.donor,x.department)
                if key in seen: frappe.throw(_("Duplicate distribution destination at row {0}.").format(row.idx))
                seen.add(key)
                if frappe.db.get_value("Project",x.project,"company") != self.company: frappe.throw(_("Distribution Project does not belong to Company at row {0}.").format(row.idx))
                if x.budget_line and frappe.db.get_value("Budget Line",x.budget_line,"project") != x.project: frappe.throw(_("Distribution Budget Line does not belong to Project at row {0}.").format(row.idx))
            pct=sum(flt(x.allocation_percentage) for x in [x for x in self.cost_distributions if x.source_row == row.name]); amt=sum(flt(x.allocated_amount) for x in [x for x in self.cost_distributions if x.source_row == row.name])
            if abs(pct-100)>0.0001: frappe.throw(_("Distribution at row {0} must equal 100%. Current total: {1}%.").format(row.idx,pct))
            if abs(amt-flt(row.net_payable))>0.01: frappe.throw(_("Distributed amount at row {0} must equal Net Payable.").format(row.idx))

    def get_source_hash(self):
        payload={"company":self.company,"posting_date":str(self.posting_date),"currency":self.currency,"lines":[{"person":r.external_person,"supplier":r.supplier,"employee":r.employee,"gross":flt(r.gross_amount),"net":flt(r.net_payable),"expense":r.expense_account,"payable":r.payable_account,"project":r.project,"cost_center":r.cost_center,"budget_line":r.budget_line,"allocation":[{"project":x.project,"cost_center":x.cost_center,"budget_line":x.budget_line,"amount":flt(x.allocated_amount)} for x in self.cost_distributions if x.source_row == r.name]} for r in self.lines if r.include]}
        return hashlib.sha256(json.dumps(payload,sort_keys=True,default=str).encode()).hexdigest()

@frappe.whitelist()
def create_draft_journal_entry(accrual):
    doc=frappe.get_doc("Service Allowance Accrual",accrual);doc.check_permission("read")
    if doc.docstatus != 1 or doc.operational_status not in ("Approved","Journal Draft Created"):
        frappe.throw(_("The accrual must be submitted and approved before creating a draft Journal Entry."))
    if not frappe.has_permission("Journal Entry","create"): frappe.throw(_("Not permitted to create Journal Entry."),frappe.PermissionError)
    if doc.journal_entry:
        status=frappe.db.get_value("Journal Entry",doc.journal_entry,"docstatus")
        if status==0:return doc.journal_entry
        frappe.throw(_("A submitted Journal Entry is already linked."))
    je=frappe.new_doc("Journal Entry");je.company=doc.company;je.posting_date=doc.posting_date;je.voucher_type="Journal Entry";je.user_remark=_("Draft accrual entry for {0}").format(doc.name)
    meta=frappe.get_meta("Journal Entry")
    if meta.has_field("custom_qorg_source_doctype"): je.custom_qorg_source_doctype="Service Allowance Accrual"
    if meta.has_field("custom_qorg_source_name"): je.custom_qorg_source_name=doc.name
    if meta.has_field("custom_qorg_source_hash"): je.custom_qorg_source_hash=doc.source_hash
    for row in doc.lines:
        if not row.include: continue
        targets=[x for x in self.cost_distributions if x.source_row == row.name] if row.allocation_treatment=="Split Distribution" else [row]
        for t in targets:
            amount=flt(t.allocated_amount) if row.allocation_treatment=="Split Distribution" else flt(row.net_payable)
            je.append("accounts",{"account":row.expense_account,"debit_in_account_currency":amount,"project":t.project,"cost_center":t.cost_center})
        party_type="Supplier" if row.supplier else ("Employee" if row.employee else None);party=row.supplier or row.employee
        account_type=frappe.db.get_value("Account",row.payable_account,"account_type")
        if account_type in ("Payable","Receivable") and not party: frappe.throw(_("A Supplier or Employee party is required for payable account {0} at row {1}. Use a non-party accrued liability account for External Person payees.").format(row.payable_account,row.idx))
        je.append("accounts",{"account":row.payable_account,"credit_in_account_currency":flt(row.net_payable),"party_type":party_type,"party":party})
    je.insert()
    doc.db_set("journal_entry",je.name,update_modified=False);doc.db_set("journal_created_on",now(),update_modified=False);doc.db_set("journal_created_by",frappe.session.user,update_modified=False);doc.db_set("operational_status","Journal Draft Created",update_modified=False)
    return je.name
