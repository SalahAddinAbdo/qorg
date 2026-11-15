from __future__ import annotations
import frappe
from frappe import _
from frappe.utils import flt
from .commitments import get_open_commitments
from .reconciliation import audit_financial_integrity

def _exists(doctype): return frappe.db.exists("DocType",doctype)
def _count(doctype,filters): return frappe.db.count(doctype,filters) if _exists(doctype) else 0
def _has(doctype,field): return bool(_exists(doctype) and frappe.get_meta(doctype).has_field(field))
def _project_count(doctype,project,extra=None):
    if not _has(doctype,"project"): return None
    filters={"project":project}; filters.update(extra or {})
    return _count(doctype,filters)

def closeout_gate(project):
    checks=[]
    def add(code,status,message,amount=0,count=0): checks.append({"code":code,"status":status,"message":message,"amount":flt(amount),"count":count})
    commitments=get_open_commitments(project=project).get("open_commitment",0)
    add("OPEN_COMMITMENTS","Blocked" if commitments>0 else "Passed","Open procurement and contractual commitments.",commitments)
    advances=_unsettled_advances(project); add("UNSETTLED_ADVANCES","Blocked" if advances>0 else "Passed","Unsettled employee advances.",advances)
    changes=_project_count("Project Change Request",project,{"docstatus":["<",2],"status":["not in",["Implemented","Closed","Rejected","Cancelled"]]}) or 0
    add("OPEN_CHANGE_REQUESTS","Blocked" if changes else "Passed","Open project change requests.",count=changes)
    _document_checks(project,add)
    _asset_stock_checks(project,add)
    _reporting_checks(project,add)
    integrity=audit_financial_integrity(project)
    add("FINANCIAL_RECONCILIATION","Blocked" if integrity["error_count"] else ("Warning" if integrity["warning_count"] else "Passed"),"Financial reconciliation findings.",count=integrity["finding_count"])
    agreements=_count("Funding Agreement",{"project":project,"docstatus":1,"status":["not in",["Closed","Cancelled"]]})
    add("GRANT_CLOSEOUT","Blocked" if agreements else "Passed","Funding agreements not financially closed.",count=agreements)
    return {"project":project,"status":"Blocked" if any(x["status"]=="Blocked" for x in checks) else ("Warning" if any(x["status"]=="Warning" for x in checks) else "Passed"),"checks":checks}

def _document_checks(project,add):
    specs=(
      ("Purchase Order",{"docstatus":1,"status":["in",["To Receive and Bill","To Bill","To Receive"]]},"OPEN_PURCHASE_ORDERS"),
      ("Purchase Invoice",{"docstatus":1,"outstanding_amount":[">",0]},"UNPAID_PURCHASE_INVOICES"),
      ("Sales Invoice",{"docstatus":1,"outstanding_amount":[">",0]},"UNPAID_SALES_INVOICES"),
      ("Journal Entry",{"docstatus":0},"DRAFT_JOURNAL_ENTRIES"),
      ("Payment Entry",{"docstatus":0},"DRAFT_PAYMENT_ENTRIES"),
      ("Stock Entry",{"docstatus":0},"DRAFT_STOCK_ENTRIES"),
    )
    for doctype,extra,code in specs:
        count=_project_count(doctype,project,extra)
        add(code,"Not Applicable" if count is None else ("Blocked" if count else "Passed"),doctype+" items requiring closure.",count=count or 0)

def _asset_stock_checks(project,add):
    for doctype,code in (("Asset Movement","OPEN_ASSET_MOVEMENTS"),("Asset Custody","OPEN_ASSET_CUSTODY"),("Stock Handover","OPEN_STOCK_HANDOVERS")):
        count=_project_count(doctype,project,{"docstatus":["<",2]})
        add(code,"Not Applicable" if count is None else ("Warning" if count else "Passed"),doctype+" records require disposition review.",count=count or 0)

def _reporting_checks(project,add):
    overdue=0; pending_receipts=0; refundable=0
    if _exists("Funding Agreement"):
        for name in frappe.get_all("Funding Agreement",filters={"project":project,"docstatus":1},pluck="name"):
            doc=frappe.get_doc("Funding Agreement",name)
            overdue += sum(1 for row in doc.reporting_schedule if row.status not in ("Submitted","Accepted") and row.due_date and str(row.due_date) <= frappe.utils.nowdate())
            pending_receipts += sum(1 for row in doc.installments if row.status not in ("Received","Cancelled") and flt(row.amount)>flt(row.received_amount))
            refundable += flt(doc.refundable_balance)
    add("OVERDUE_DONOR_REPORTS","Blocked" if overdue else "Passed","Overdue donor reports.",count=overdue)
    add("OUTSTANDING_FUNDING_INSTALLMENTS","Warning" if pending_receipts else "Passed","Funding installments not fully received.",count=pending_receipts)
    add("REFUNDABLE_BALANCE","Blocked" if refundable else "Passed","Refundable donor balance must be cleared before closeout.",amount=refundable)

def refresh_project_closeout(doc,method=None):
    if not doc.get("project"): return
    gate=closeout_gate(doc.project)
    for field,code in (("open_commitments_amount","OPEN_COMMITMENTS"),("unsettled_advances_amount","UNSETTLED_ADVANCES")):
        if doc.meta.has_field(field): doc.set(field,next(x["amount"] for x in gate["checks"] if x["code"]==code))
    if doc.meta.has_field("financial_closeout_status"): doc.financial_closeout_status=gate["status"]
    return gate

def validate_project_closeout(doc,method=None):
    gate=refresh_project_closeout(doc)
    if not gate:return
    if doc.get("financial_closeout_completed") and gate["status"]=="Blocked":
        frappe.throw(_("Financial closeout is blocked by: {0}.").format(", ".join(x["code"] for x in gate["checks"] if x["status"]=="Blocked")))
    if doc.get("grant_closeout_completed") and not doc.get("financial_closeout_completed"): frappe.throw(_("Grant closeout requires Financial Closeout Completed."))

def _unsettled_advances(project):
    if not _exists("Employee Advance"):return 0
    meta=frappe.get_meta("Employee Advance")
    if not all(meta.has_field(x) for x in ("project","advance_amount","paid_amount")):return 0
    return flt(frappe.db.sql("select coalesce(sum(greatest(advance_amount-paid_amount,0)),0) from `tabEmployee Advance` where docstatus=1 and project=%s",project)[0][0])
