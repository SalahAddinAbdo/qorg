import frappe
from frappe import _
from frappe.utils import flt
from frappe.utils import cint


@frappe.whitelist()
def get_company_defaults(company):
    if not company:return {}
    row=frappe.db.get_value("Company",company,["default_currency","custom_enable_shared_cost_allocation","custom_shared_cost_default_cost_center","custom_indirect_cost_expense_account","custom_indirect_cost_recovery_account","custom_payroll_account_group","custom_require_allocation_before_project_closeout","custom_allow_post_closeout_adjustment"],as_dict=True) or {}
    return row

@frappe.whitelist()
def get_target_defaults(project=None,budget_line=None,funding_agreement=None,company=None):
    result={"project":project,"budget_line":budget_line,"funding_agreement":funding_agreement}
    if project:
        p=frappe.db.get_value("Project",project,["company","cost_center","status"],as_dict=True) or {}
        if company and p.get("company")!=company:frappe.throw(_("Project {0} does not belong to Company {1}.").format(project,company))
        result.update({"project_company":p.get("company"),"cost_center":p.get("cost_center"),"project_status":p.get("status")})
    if budget_line:
        bl=frappe.db.get_value("Budget Line",budget_line,["project","funding_agreement","donor_currency","base_currency","eligibility_start_date","eligibility_end_date","line_cost","status","is_group"],as_dict=True) or {}
        if project and bl.get("project")!=project:frappe.throw(_("Budget Line does not belong to the selected Project."))
        if bl.get("is_group"):frappe.throw(_("A group Budget Line cannot receive an allocation."))
        result.update({"budget_line_project":bl.get("project"),"funding_agreement":funding_agreement or bl.get("funding_agreement"),"budget_line_status":bl.get("status"),"budget_amount":bl.get("line_cost"),"eligibility_start_date":bl.get("eligibility_start_date"),"eligibility_end_date":bl.get("eligibility_end_date")})
    agreement=result.get("funding_agreement")
    if agreement:
        fa=frappe.db.get_value("Funding Agreement",agreement,["project","company","donor","agreement_currency","indirect_cost_percent","eligibility_start_date","eligibility_end_date","status","exchange_rate","exchange_rate_date","exchange_rate_source"],as_dict=True) or {}
        if project and fa.get("project")!=project:frappe.throw(_("Funding Agreement does not belong to the selected Project."))
        if company and fa.get("company")!=company:frappe.throw(_("Funding Agreement does not belong to the selected Company."))
        result.update({"donor":fa.get("donor"),"donor_currency":fa.get("agreement_currency"),"indirect_rate_override":fa.get("indirect_cost_percent"),"eligibility_start_date":fa.get("eligibility_start_date") or result.get("eligibility_start_date"),"eligibility_end_date":fa.get("eligibility_end_date") or result.get("eligibility_end_date"),"agreement_status":fa.get("status"),"donor_exchange_rate":fa.get("exchange_rate"),"exchange_rate_date":fa.get("exchange_rate_date"),"exchange_rate_source":fa.get("exchange_rate_source")})
    return result

@frappe.whitelist()
def get_rule_defaults(rule):
    if not rule:return {}
    doc=frappe.get_doc("Shared Cost Allocation Rule",rule);doc.check_permission("read")
    return {"company":doc.company,"allocation_category":doc.allocation_category,"allocation_method":doc.allocation_method,"source_cost_center":doc.source_cost_center or frappe.get_cached_value("Company",doc.company,"custom_shared_cost_default_cost_center"),"period_start":doc.effective_from,"period_end":doc.effective_to,"posting_date":doc.effective_from,"currency":frappe.get_cached_value("Company",doc.company,"default_currency")}


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def search_eligible_source_vouchers(doctype, txt, searchfield, start, page_len, filters):
    """Return submitted vouchers that contain at least one GL row eligible for the rule source."""
    filters = frappe.parse_json(filters) if isinstance(filters, str) else (filters or {})
    company = filters.get("company")
    voucher_type = filters.get("voucher_type") or doctype
    source_cost_center = filters.get("source_cost_center")
    source_project = filters.get("source_project")
    require_unassigned = cint(filters.get("require_unassigned_project"))
    finance_book = filters.get("finance_book")
    if not company or not voucher_type or not source_cost_center:
        return []
    if not frappe.has_permission(voucher_type, "read"):
        return []
    if source_project and require_unassigned:
        return []

    conditions = [
        "gle.company = %(company)s",
        "gle.voucher_type = %(voucher_type)s",
        "gle.cost_center = %(source_cost_center)s",
        "gle.is_cancelled = 0",
        "(gle.debit - gle.credit) > 0.005",
        "acc.root_type = 'Expense'",
        "acc.is_group = 0",
        "gle.voucher_no like %(txt)s",
    ]
    values = {
        "company": company,
        "voucher_type": voucher_type,
        "source_cost_center": source_cost_center,
        "txt": f"%{txt or ''}%",
        "start": cint(start),
        "page_len": max(1, min(cint(page_len) or 20, 100)),
    }
    if source_project:
        conditions.append("gle.project = %(source_project)s")
        values["source_project"] = source_project
    elif require_unassigned:
        conditions.append("coalesce(gle.project, '') = ''")
    if finance_book:
        conditions.append("coalesce(gle.finance_book, '') = %(finance_book)s")
        values["finance_book"] = finance_book

    # Exclude allocation-generated and reversal journals to prevent circular allocation.
    conditions.append("not exists (select 1 from `tabShared Cost Allocation Run` r where r.docstatus = 1 and (r.journal_entry = gle.voucher_no or r.reversal_journal_entry = gle.voucher_no))")
    sql = f"""
        select
            gle.voucher_no,
            max(gle.posting_date) as posting_date,
            group_concat(distinct gle.account order by gle.account separator ', ') as accounts,
            round(sum(gle.debit - gle.credit), 2) as eligible_amount
        from `tabGL Entry` gle
        inner join `tabAccount` acc on acc.name = gle.account and acc.company = gle.company
        where {' and '.join(conditions)}
        group by gle.voucher_type, gle.voucher_no
        order by max(gle.posting_date) desc, gle.voucher_no desc
        limit %(start)s, %(page_len)s
    """
    return frappe.db.sql(sql, values)
