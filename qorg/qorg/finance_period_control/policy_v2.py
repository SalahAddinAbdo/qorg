import frappe
from frappe import _
from frappe.utils import flt
from qorg.qorg.finance_period_control.actuals import actual_for_line
from qorg.qorg.finance_period_control.period_balances import open_commitment_for_period
from qorg.qorg.finance_period_control.service import resolve_budget_period


def policy(company,project=None):
    p=project and frappe.db.get_value("Project",project,"qorg_budget_control_policy")
    if p=="Disabled":return "Disabled"
    if p in ("Warn","Stop"):return p
    company_enabled=frappe.db.get_value("Company",company,"qorg_enable_period_budget_control")
    global_enabled=frappe.db.get_single_value("Accounts Settings","qorg_enable_period_budget_control")
    if not (company_enabled or global_enabled):return "Disabled"
    action=frappe.db.get_value("Company",company,"qorg_commitment_control_action")
    if action in ("Warn","Stop"):return action
    return frappe.db.get_single_value("Accounts Settings","qorg_commitment_control_action") or "Stop"

def check_period_flags(period,transaction_type):
    if transaction_type=="Commitment" and not period.allow_commitments:frappe.throw(_("Budget Period {0} does not allow commitments").format(period.name))
    if transaction_type=="Actual" and not period.allow_actuals:frappe.throw(_("Budget Period {0} does not allow actual postings").format(period.name))

def evaluate(company,project,budget_line,posting_date,pending_amount,reference_doctype=None):
    mode=policy(company,project)
    if mode=="Disabled":return {"policy":mode,"allowed":True}
    period,source=resolve_budget_period(company,posting_date,project,require_open=True,reference_doctype=reference_doctype,transaction_type="Commitment")
    check_period_flags(period,"Commitment")
    budget=flt(frappe.db.sql("select coalesce(sum(allocated_amount),0) from `tabBudget Period Allocation` where parent=%s and budget_period=%s",(budget_line,period.name))[0][0])
    actual=actual_for_line(company,budget_line,period.from_date,period.to_date)
    committed=open_commitment_for_period(budget_line,period.name,company)
    available=budget-actual-committed;after=available-flt(pending_amount)
    result={"policy":mode,"period":period.name,"period_source":source,"budget":budget,"actual":actual,"commitment":committed,"pending":flt(pending_amount),"available_before":available,"available_after":after,"allowed":after>=-0.005}
    if not result["allowed"]:
        msg=_("Budget control {0}: Budget Line {1}, Period {2}, available {3}, requested {4}, shortage {5}").format(mode,budget_line,period.name,available,pending_amount,abs(after))
        if mode=="Stop":frappe.throw(msg)
        frappe.msgprint(msg,title=_("Budget Warning"),indicator="orange")
    return result

def validate_document(doc,method=None):
    if doc.docstatus>0 or doc.get("is_return"):return
    grouped={}
    from qorg.qorg.finance_period_control.amount_policy import calculate_row_amount
    from qorg.qorg.finance_period_control.source_reconciliation import row_budget_line
    for row in doc.get("items") or []:
        bl=row_budget_line(row);project=row.get("project") or doc.get("project")
        if not bl or not project:continue
        amount=calculate_row_amount(doc,row,bl)["base_amount"]
        grouped[(project,bl)]=grouped.get((project,bl),0)+amount
    date=doc.get("posting_date") or doc.get("transaction_date") or frappe.utils.today()
    for (project,bl),amount in grouped.items():evaluate(doc.company,project,bl,date,amount,doc.doctype)
