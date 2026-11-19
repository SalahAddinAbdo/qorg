import frappe
from frappe import _
from frappe.utils import flt, getdate

def validate_rule(doc):
    _clear_inapplicable_values(doc)
    if doc.effective_to and getdate(doc.effective_to) < getdate(doc.effective_from): frappe.throw(_("Effective To cannot be before Effective From."))
    if doc.source_project and doc.require_unassigned_project: frappe.throw(_("Select either a Source Project or Require Unassigned Project, not both."))
    selected_seen=set()
    for row in doc.selected_vouchers or []:
        key=(row.voucher_type,row.voucher_no)
        if key in selected_seen: frappe.throw(_("Duplicate selected voucher {0} {1} at row {2}.").format(row.voucher_type,row.voucher_no,row.idx))
        selected_seen.add(key)
    active=[r for r in doc.targets if r.allow_allocation]
    if not active: frappe.throw(_("At least one eligible allocation target is required."))
    seen=set()
    for row in active:
        key=(row.project,row.cost_center,row.budget_line,row.funding_agreement or "")
        if key in seen: frappe.throw(_("Duplicate allocation target at row {0}.").format(row.idx))
        seen.add(key); _validate_target(doc,row)
    if doc.allocation_method=="Fixed Percentage":
        total=sum(flt(r.allocation_percentage) for r in active)
        if abs(total-100)>0.0001: frappe.throw(_("Allocation percentages must equal 100%. Current total: {0}%. Difference: {1}%.").format(total,100-total))
    elif doc.allocation_method=="Fixed Amount" and sum(flt(r.fixed_amount) for r in active)<=0: frappe.throw(_("Fixed amounts must be greater than zero."))
    elif doc.allocation_method in ("Manual Driver","Headcount","Beneficiary Count") and doc.allocation_method=="Manual Driver" and sum(flt(r.driver_quantity) for r in active)<=0: frappe.throw(_("Driver quantities must total more than zero."))
    elif doc.allocation_method=="Composite Driver":
        total=sum(flt(doc.get(x)) for x in ("direct_expenditure_weight","budget_weight","headcount_weight","beneficiary_weight","manual_weight"))
        if abs(total-100)>0.0001: frappe.throw(_("Composite driver weights must equal 100%. Current total: {0}%.").format(total))
    if doc.source_selection_mode=="Selected Vouchers Only" and not any(r.include for r in doc.selected_vouchers): frappe.throw(_("At least one included source voucher is required."))
    if doc.allocation_category=="Indirect Cost Recovery": _validate_indirect(doc)
    _validate_version(doc)

def _validate_target(doc,row):
    if row.target_effective_to and row.target_effective_from and getdate(row.target_effective_to)<getdate(row.target_effective_from): frappe.throw(_("Target Effective To cannot be before Target Effective From at row {0}.").format(row.idx))
    project=frappe.db.get_value("Project",row.project,["company","status"],as_dict=True)
    if not project or project.company!=doc.company: frappe.throw(_("Target project at row {0} must belong to company {1}.").format(row.idx,doc.company))
    if project.status in ("Cancelled","Completed"): frappe.throw(_("Closed or cancelled projects cannot be added to a new allocation rule."))
    bl=frappe.db.get_value("Budget Line",row.budget_line,["project","funding_agreement"],as_dict=True)
    if not bl or bl.project!=row.project: frappe.throw(_("Budget Line at row {0} does not belong to the selected Project.").format(row.idx))
    if row.funding_agreement:
        fa=frappe.db.get_value("Funding Agreement",row.funding_agreement,["project","donor","eligibility_start_date","eligibility_end_date","status"],as_dict=True)
        if not fa or fa.project!=row.project: frappe.throw(_("Funding Agreement at row {0} does not belong to the selected Project.").format(row.idx))
        if fa.status not in ("Active",): frappe.throw(_("Funding Agreement at row {0} is not active for allocation.").format(row.idx))
        row.donor=fa.donor;row.eligibility_start_date=fa.eligibility_start_date;row.eligibility_end_date=fa.eligibility_end_date
    elif bl.funding_agreement: row.funding_agreement=bl.funding_agreement

def _validate_indirect(doc):
    if not doc.indirect_cost_expense_account or not doc.indirect_cost_recovery_account: frappe.throw(_("Indirect Cost Expense Account and Indirect Cost Recovery Account are required."))
    if not doc.rate_periods: frappe.throw(_("At least one effective-dated indirect cost rate is required."))
    periods=sorted(doc.rate_periods,key=lambda x:getdate(x.effective_from))
    for i,row in enumerate(periods):
        if flt(row.indirect_cost_rate)<0: frappe.throw(_("Indirect cost rate cannot be negative."))
        if row.effective_to and getdate(row.effective_to)<getdate(row.effective_from): frappe.throw(_("Rate period end date cannot be before its start date."))
        if i and (not periods[i-1].effective_to or getdate(row.effective_from)<=getdate(periods[i-1].effective_to)): frappe.throw(_("Indirect cost rate periods cannot overlap."))

def _validate_version(doc):
    if doc.supersedes_rule:
        old=frappe.get_doc("Shared Cost Allocation Rule",doc.supersedes_rule)
        if old.company!=doc.company or old.allocation_category!=doc.allocation_category: frappe.throw(_("The superseded rule must have the same Company and Allocation Category."))
        if not doc.change_effective_date or not doc.change_reason: frappe.throw(_("Change Effective Date and Change Reason are required for a rule amendment."))
        if doc.change_type in ("Donor Approved Increase","Donor Approved Reduction") and not doc.donor_approval_reference: frappe.throw(_("Donor Approval Reference is required for a donor-approved change."))


def _clear_inapplicable_values(doc):
    if doc.allocation_category!="Indirect Cost Recovery":
        doc.indirect_base_method=None;doc.indirect_cost_expense_account=None;doc.indirect_cost_recovery_account=None;doc.total_recovery_cap=0;doc.exclude_shared_cost_allocations_from_base=0;doc.set("rate_periods",[])
    if doc.source_selection_mode=="Filtered GL Entries":doc.set("selected_vouchers",[])
    elif doc.source_selection_mode=="Selected Vouchers Only":doc.set("source_filters",[]);doc.voucher_types=None
    for row in doc.targets:
        if doc.allocation_method!="Fixed Percentage":row.allocation_percentage=0
        if doc.allocation_method!="Fixed Amount":row.fixed_amount=0
        if doc.allocation_method not in ("Manual Driver","Composite Driver"):row.driver_quantity=0
    if doc.allocation_method!="Composite Driver":
        for field in ("direct_expenditure_weight","budget_weight","headcount_weight","beneficiary_weight","manual_weight"):doc.set(field,0)
