import frappe
from frappe import _
from frappe.utils import flt,getdate
from .calculation import eligible_split

def donor_for_agreement(agreement):
    if not agreement:return None
    meta=frappe.get_meta("Funding Agreement")
    for field in ("donor","funding_source","primary_donor"):
        if meta.has_field(field):
            value=frappe.db.get_value("Funding Agreement",agreement,field)
            if value:return value
def _value(doc,names):
    for name in names:
        if doc.meta.has_field(name) and doc.get(name) not in (None,""):return doc.get(name)
def _issue(code,message,reference_type=None,reference=None):return {"code":code,"message":message,"reference_type":reference_type,"reference":reference}
def _project_issues(name,on_date,company):
    out=[]
    if not name:return [_issue("MISSING_PROJECT",_("Project is required."),"Project",name)]
    doc=frappe.get_doc("Project",name)
    if company and doc.get("company") and doc.company!=company:out.append(_issue("PROJECT_COMPANY",_("Project belongs to another company."),"Project",name))
    status=doc.get("status")
    if status in ("Cancelled","Completed","Closed"):out.append(_issue("PROJECT_CLOSED",_("Project is not open for payroll allocation."),"Project",name))
    start=_value(doc,("expected_start_date","start_date","custom_start_date"));end=_value(doc,("expected_end_date","end_date","custom_end_date"))
    if start and getdate(on_date)<getdate(start):out.append(_issue("PROJECT_NOT_STARTED",_("Payroll date precedes the Project start date."),"Project",name))
    if end and getdate(on_date)>getdate(end):out.append(_issue("PROJECT_ENDED",_("Payroll date exceeds the Project end date."),"Project",name))
    for field in ("custom_closure_status","closure_status","custom_project_closure_status"):
        if doc.meta.has_field(field) and doc.get(field) in ("Closed","Final Closed","Locked"):out.append(_issue("PROJECT_CLOSURE_LOCK",_("Project closure prevents new payroll allocation."),"Project",name));break
    return out
def _agreement_issues(name,project,on_date):
    if not name:return []
    out=[];doc=frappe.get_doc("Funding Agreement",name)
    if doc.docstatus!=1:out.append(_issue("AGREEMENT_NOT_SUBMITTED",_("Funding Agreement is not submitted."),"Funding Agreement",name))
    status=_value(doc,("status","funding_status","agreement_status"))
    if status in ("Cancelled","Closed","Expired","Terminated"):out.append(_issue("AGREEMENT_INACTIVE",_("Funding Agreement is not active."),"Funding Agreement",name))
    linked=_value(doc,("project","operating_project"))
    if linked and project and linked!=project:out.append(_issue("AGREEMENT_PROJECT",_("Funding Agreement is not linked to the selected Project."),"Funding Agreement",name))
    start=_value(doc,("eligibility_start_date","start_date","valid_from"));end=_value(doc,("eligibility_end_date","end_date","valid_to"))
    if start and getdate(on_date)<getdate(start):out.append(_issue("AGREEMENT_NOT_ELIGIBLE",_("Funding Agreement is not yet eligible."),"Funding Agreement",name))
    if end and getdate(on_date)>getdate(end):out.append(_issue("AGREEMENT_EXPIRED",_("Funding Agreement eligibility period has ended."),"Funding Agreement",name))
    return out
def _budget_issues(name,project,agreement):
    if not name:return []
    out=[];doc=frappe.get_doc("Budget Line",name)
    if doc.get("is_group"):out.append(_issue("BUDGET_LINE_GROUP",_("Budget Line must be a leaf line."),"Budget Line",name))
    linked=_value(doc,("project",))
    if linked and project and linked!=project:out.append(_issue("BUDGET_PROJECT",_("Budget Line is not linked to the selected Project."),"Budget Line",name))
    linked_agreement=_value(doc,("funding_agreement",))
    if linked_agreement and agreement and linked_agreement!=agreement:out.append(_issue("BUDGET_AGREEMENT",_("Budget Line is not linked to the selected Funding Agreement."),"Budget Line",name))
    status=_value(doc,("status","approval_status"))
    if status in ("Draft","Rejected","Closed","Cancelled","Superseded"):out.append(_issue("BUDGET_NOT_APPROVED",_("Budget Line is not approved for allocation."),"Budget Line",name))
    return out
def validate_destination_details(destination,on_date,company=None,amount=None):
    project=destination.get("project");agreement=destination.get("funding_agreement");line=destination.get("budget_line")
    issues=_project_issues(project,on_date,company)+_agreement_issues(agreement,project,on_date)+_budget_issues(line,project,agreement)
    return issues
def validate_destination(destination,on_date,company=None,amount=None):return [x["message"] for x in validate_destination_details(destination,on_date,company,amount)]
def available_budget(budget_line,exclude_run=None):
    if not budget_line:return None
    doc=frappe.get_doc("Budget Line",budget_line)
    # If QOrg exposes available_amount, it is already net of actuals and commitments.
    if doc.meta.has_field("available_amount") and doc.get("available_amount") not in (None,""):
        available=flt(doc.get("available_amount"))
        payroll=flt(frappe.db.sql("""select coalesce(sum(r.company_currency_amount),0) from `tabPayroll Allocation Result` r inner join `tabPayroll Allocation Run` p on p.name=r.parent where r.budget_line=%s and p.docstatus=1 and p.status='Approved' and (%s='' or p.name!=%s)""",(budget_line,exclude_run or '',exclude_run or ''))[0][0])
        return {"source":"Budget Line.available_amount","approved":None,"actual":None,"other_commitments":None,"payroll_reserved":payroll,"available":available-payroll}
    approved=flt(_value(doc,("current_approved_amount","approved_amount","line_cost","base_amount")))
    if not approved:frappe.throw(_("Budget Line {0} has no supported approved-budget field.").format(budget_line))
    actual=0
    if frappe.get_meta("GL Entry").has_field("budget_line"):
        actual=flt(frappe.db.sql("select coalesce(sum(debit-credit),0) from `tabGL Entry` where budget_line=%s and is_cancelled=0",budget_line)[0][0])
    other=flt(_value(doc,("committed_amount","commitment_amount","reserved_adjustment")))
    payroll=flt(frappe.db.sql("""select coalesce(sum(r.company_currency_amount),0) from `tabPayroll Allocation Result` r inner join `tabPayroll Allocation Run` p on p.name=r.parent where r.budget_line=%s and p.docstatus=1 and p.status in ('Approved','Posted','Reconciled','Closed') and (%s='' or p.name!=%s)""",(budget_line,exclude_run or '',exclude_run or ''))[0][0])
    return {"source":"composed","approved":approved,"actual":actual,"other_commitments":other,"payroll_reserved":payroll,"available":approved-actual-other-payroll}
def eligible_amount(amount,rule,precision):
    eligible,_=eligible_split(amount,rule.eligible_percentage or 100,rule.maximum_eligible_amount,precision);return float(eligible)
