from __future__ import annotations
import frappe
from frappe.utils import flt
from .actuals import get_posted_actual
from .commitments import get_open_commitments

ERROR = "Error"
WARNING = "Warning"
INFO = "Information"

def _finding(severity, code, doctype, name, project, message, amount=0, expected=None, actual=None, currency=None):
    return {"severity":severity,"code":code,"reference_doctype":doctype,"reference_name":name,"project":project,"amount":flt(amount),"expected_value":expected,"actual_value":actual,"currency":currency,"message":message}

def audit_financial_integrity(project=None):
    findings=[]; values={"project":project} if project else {}; clause=" and gle.project=%(project)s" if project else ""
    gl_meta=frappe.get_meta("GL Entry")
    if gl_meta.has_field("budget_line"):
        rows=frappe.db.sql(f"""select gle.name,gle.project,gle.budget_line,gle.voucher_type,gle.voucher_no,gle.posting_date
            from `tabGL Entry` gle where gle.is_cancelled=0 and ifnull(gle.project,'')!=''
            and ifnull(gle.budget_line,'')='' {clause}""",values,as_dict=True)
        for row in rows: findings.append(_finding(ERROR,"GL_WITHOUT_BUDGET_LINE","GL Entry",row.name,row.project,"Posted project ledger entry has no Budget Line."))
        rows=frappe.db.sql(f"""select gle.name,gle.project,gle.budget_line,gle.posting_date,bl.project line_project,
            bl.eligibility_start_date,bl.eligibility_end_date from `tabGL Entry` gle
            inner join `tabBudget Line` bl on bl.name=gle.budget_line
            where gle.is_cancelled=0 {clause}""",values,as_dict=True)
        for row in rows:
            if row.project != row.line_project: findings.append(_finding(ERROR,"PROJECT_BUDGET_LINE_MISMATCH","GL Entry",row.name,row.project,"Budget Line belongs to another project."))
            if row.eligibility_start_date and row.posting_date < row.eligibility_start_date: findings.append(_finding(ERROR,"BEFORE_ELIGIBILITY","GL Entry",row.name,row.project,"Posting date is before the eligibility period."))
            if row.eligibility_end_date and row.posting_date > row.eligibility_end_date: findings.append(_finding(ERROR,"AFTER_ELIGIBILITY","GL Entry",row.name,row.project,"Posting date is after the eligibility period."))
    line_filters={"project":project} if project else {}
    line_fields=["name","project","line_cost"]
    meta=frappe.get_meta("Budget Line")
    for optional in ("original_approved_amount","funding_agreement","currency"):
        if meta.has_field(optional): line_fields.append(optional)
    for line in frappe.get_all("Budget Line",filters=line_filters,fields=line_fields):
        actual=get_posted_actual(project=line.project,budget_line=line.name)
        commitment=get_open_commitments(project=line.project,budget_line=line.name).get("open_commitment",0)
        excess=actual+commitment-flt(line.line_cost)
        if excess>0: findings.append(_finding(ERROR,"BUDGET_EXCEEDED","Budget Line",line.name,line.project,"Actual expenditure and open commitments exceed the approved budget.",excess,line.line_cost,actual+commitment,line.get("currency")))
        if "original_approved_amount" in line and flt(line.original_approved_amount)<0: findings.append(_finding(ERROR,"INVALID_ORIGINAL_BUDGET","Budget Line",line.name,line.project,"Original approved amount cannot be negative."))
    if frappe.db.exists("DocType","Funding Agreement"):
        filters={"project":project} if project else {}
        for agreement in frappe.get_all("Funding Agreement",filters=filters,fields=["name","project","donor","agreement_amount","agreement_currency","refundable_balance","status","docstatus"]):
            rows=frappe.get_all("Project Funding Source",filters={"parent":agreement.project,"parenttype":"Project","funding_agreement":agreement.name},fields=["name","approved_amount_donor_currency"])
            allocated=sum(flt(row.approved_amount_donor_currency) for row in rows)
            if allocated and abs(allocated-flt(agreement.agreement_amount))>0.01:
                findings.append(_finding(WARNING,"AGREEMENT_ALLOCATION_MISMATCH","Funding Agreement",agreement.name,agreement.project,"Project Funding Source allocation does not match the agreement value.",abs(allocated-flt(agreement.agreement_amount)),agreement.agreement_amount,allocated,agreement.agreement_currency))
            if agreement.status=="Closed" and flt(agreement.refundable_balance)>0:
                findings.append(_finding(ERROR,"REFUNDABLE_BALANCE_OPEN","Funding Agreement",agreement.name,agreement.project,"Closed agreement still has a refundable balance.",agreement.refundable_balance,currency=agreement.agreement_currency))
    if frappe.db.exists("DocType","Budget Transfer Audit"):
        filters={"project":project} if project else {}
        for audit in frappe.get_all("Budget Transfer Audit",filters=filters,fields=["name","project","project_change_request","reversed_on"]):
            applied=frappe.db.get_value("Project Change Request",audit.project_change_request,["change_applied","budget_transfer_audit"],as_dict=True)
            if not applied or applied.budget_transfer_audit!=audit.name:
                findings.append(_finding(ERROR,"TRANSFER_AUDIT_LINK_MISMATCH","Budget Transfer Audit",audit.name,audit.project,"Budget Transfer Audit is not linked consistently to its Project Change Request."))
    return {"project":project,"finding_count":len(findings),"error_count":sum(x["severity"]==ERROR for x in findings),"warning_count":sum(x["severity"]==WARNING for x in findings),"findings":findings,"passed":not any(x["severity"]==ERROR for x in findings)}
