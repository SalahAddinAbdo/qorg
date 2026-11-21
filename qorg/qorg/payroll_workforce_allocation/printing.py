import frappe
from frappe import _
from .permissions import can_view_funding_amounts
DISCLOSURE_LEVELS=("None","Project and Percentage","Project, Funding and Percentage","Full Authorized Disclosure")
def _title(dt,name):
    if not name:return None
    meta=frappe.get_meta(dt);title=meta.get_title_field() if hasattr(meta,"get_title_field") else None
    return frappe.db.get_value(dt,name,title) if title else name
def funding_statement_context(salary_slip,user=None):
    user=user or frappe.session.user;slip=frappe.get_doc("Salary Slip",salary_slip)
    if user==frappe.session.user:
        permitted=slip.has_permission("read")
    else:
        permitted=frappe.has_permission("Salary Slip",ptype="read",doc=slip,user=user)
    if not permitted:frappe.throw(_("Not permitted to view this Salary Slip."),frappe.PermissionError)
    company=frappe.get_doc("Company",slip.company);level=company.get("custom_employee_funding_disclosure_level") or "Project and Percentage"
    legacy={"Do Not Show Funding Details":"None","Project, Donor and Percentage":"Project, Funding and Percentage","Full Funding Details":"Full Authorized Disclosure","Percentage Only":"Project and Percentage"};level=legacy.get(level,level)
    if level=="Full Authorized Disclosure" and not can_view_funding_amounts(user):level="Project, Funding and Percentage"
    rows=frappe.get_all("Payroll Allocation Result",filters={"salary_slip":salary_slip,"parenttype":"Payroll Allocation Run","docstatus":1},fields=["project","funding_agreement","budget_line","work_share","company_currency_amount","currency"],limit_page_length=0);grouped={}
    for x in rows:
        key=(x.project,x.funding_agreement,x.budget_line,x.currency);g=grouped.setdefault(key,{"project":x.project,"project_title":_title("Project",x.project),"funding_agreement":x.funding_agreement,"funding_title":_title("Funding Agreement",x.funding_agreement),"budget_line":x.budget_line,"percentage":0,"amount":0,"currency":x.currency});g["percentage"]+=x.work_share or 0;g["amount"]+=x.company_currency_amount or 0
    return {"salary_slip":slip,"company":company,"disclosure_level":level,"rows":[] if level=="None" else list(grouped.values()),"show_project":level in ("Project and Percentage","Project, Funding and Percentage","Full Authorized Disclosure"),"show_funding":level in ("Project, Funding and Percentage","Full Authorized Disclosure"),"show_amounts":level=="Full Authorized Disclosure","rtl":frappe.local.lang in ("ar","fa","he","ur")}
@frappe.whitelist()
def allocation_summary(salary_slip):return funding_statement_context(salary_slip)
