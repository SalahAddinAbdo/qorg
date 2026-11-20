from __future__ import annotations
import frappe
from frappe import _
from frappe.utils import flt, getdate

def validate_distribution_rows(doc,table_field,source_rows,require_all=False):
    rows=doc.get(table_field) or [];grouped={}
    for row in rows:
        if not row.source_key:frappe.throw(_("Source Key is required at distribution row {0}.").format(row.idx))
        grouped.setdefault(row.source_key,[]).append(row)
        if frappe.db.get_value("Project",row.project,"company") != doc.company:frappe.throw(_("Project at distribution row {0} does not belong to Company.").format(row.idx))
        if row.cost_center and frappe.db.get_value("Cost Center",row.cost_center,"company") != doc.company:frappe.throw(_("Cost Center at distribution row {0} does not belong to Company.").format(row.idx))
        if row.budget_line and frappe.db.get_value("Budget Line",row.budget_line,"project") != row.project:frappe.throw(_("Budget Line at distribution row {0} does not belong to Project.").format(row.idx))
        if row.funding_agreement:
            agreement=frappe.db.get_value("Funding Agreement",row.funding_agreement,["project","docstatus","status","donor","company","eligibility_start_date","eligibility_end_date","start_date","end_date"],as_dict=True) or {}
            if agreement.get("project") and agreement.get("project") != row.project:frappe.throw(_("Funding Agreement at distribution row {0} does not belong to Project.").format(row.idx))
            if agreement.get("docstatus") != 1:frappe.throw(_("Funding Agreement at distribution row {0} must be submitted.").format(row.idx))
            _validate_agreement_eligibility(doc,row,agreement)
        if row.manual_override and not row.override_reason:frappe.throw(_("Override Reason is required at distribution row {0}.").format(row.idx))
    for source_name,source in source_rows.items():
        dist=grouped.get(source_name,[])
        if not dist:
            if require_all:frappe.throw(_("Distribution is required for source row {0}.").format(source.idx))
            continue
        seen=set()
        for row in dist:
            key=(row.project,row.cost_center,row.budget_line,row.funding_agreement,row.donor,row.department)
            if key in seen:frappe.throw(_("Duplicate target dimensions for source row {0}.").format(source.idx))
            seen.add(key)
        base_rows=[flt(x.base_amount) for x in dist]
        source_base=flt(source.get("base_net_amount") or source.get("base_amount"))
        if source_base and any(base_rows) and abs(sum(base_rows)-source_base)>0.01:frappe.throw(_("Base-currency distribution for source row {0} must equal {1}. Current total: {2}.").format(source.idx,source_base,sum(base_rows)))
        total=sum(flt(x.allocated_amount) for x in dist);pct=sum(flt(x.allocation_percentage) for x in dist)
        source_amount=flt(source.get("net_amount") or source.get("amount") or source.get("base_amount"))
        if abs(total-source_amount)>0.01:frappe.throw(_("Distribution for source row {0} must equal {1}. Current total: {2}.").format(source.idx,source_amount,total))
        if abs(pct-100)>0.0001:frappe.throw(_("Distribution percentages for source row {0} must equal 100%. Current total: {1}%.").format(source.idx,pct))


BLOCKED_AGREEMENT_STATUSES = ("Suspended", "Closed", "Cancelled", "Draft", "Under Review")


def _validate_agreement_eligibility(doc, row, agreement):
    """Funding Agreement must be usable on the document date and for the same donor/company."""
    if agreement.get("status") in BLOCKED_AGREEMENT_STATUSES:
        frappe.throw(_("Funding Agreement at distribution row {0} has status {1} and cannot receive costs.").format(row.idx, agreement.get("status")))
    if agreement.get("company") and agreement.get("company") != doc.company:
        frappe.throw(_("Funding Agreement at distribution row {0} does not belong to Company.").format(row.idx))
    if row.donor and agreement.get("donor") and row.donor != agreement.get("donor"):
        frappe.throw(_("Donor at distribution row {0} does not match the Funding Agreement donor.").format(row.idx))
    posting = doc.get("posting_date") or doc.get("transaction_date")
    if not posting:
        return
    start = agreement.get("eligibility_start_date") or agreement.get("start_date")
    end = agreement.get("eligibility_end_date") or agreement.get("end_date")
    if start and getdate(posting) < getdate(start):
        frappe.throw(_("Posting date {0} is before the Funding Agreement eligibility start {1} at row {2}.").format(posting, start, row.idx))
    if end and getdate(posting) > getdate(end):
        frappe.throw(_("Posting date {0} is after the Funding Agreement eligibility end {1} at row {2}.").format(posting, end, row.idx))
