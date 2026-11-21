import frappe
from frappe import _
from frappe.utils import flt
from .allocator import calculate_document
from .posting import create_reclassification_entry, create_reversal_entry
from .reconciliation import reconcile_run
from .utils import payroll_source_fingerprint
from .events import update_source_status
from .reservations import lock_payroll_entry, reserve_run, release_run, mark_posted
from .audit_snapshot import build_snapshot

ALLOWED_ACTIONS={"Draft":{"calculate"},"Calculated":{"calculate","approve"},"Exceptions Found":{"calculate"},"Ready for Approval":{"calculate","approve"},"Approved":{"post"},"Posted":{"reconcile","reverse"},"Reconciled":{"close","reverse"},"Closed":{"reverse"}}

def validate_run(doc):
    if not doc.payroll_entry:return
    payroll=frappe.get_doc("Payroll Entry",doc.payroll_entry)
    if payroll.docstatus!=1:frappe.throw(_("Payroll Entry must be submitted."))
    duplicate=frappe.db.exists("Payroll Allocation Run",{"payroll_entry":doc.payroll_entry,"name":["!=",doc.name],"docstatus":["<",2],"status":["not in",["Reversed","Cancelled"]]})
    if duplicate:frappe.throw(_("An active Payroll Allocation Run already exists: {0}").format(duplicate))
    doc.company=payroll.company;doc.start_date=payroll.start_date;doc.end_date=payroll.end_date

def _assert_action(doc,action):
    if action not in ALLOWED_ACTIONS.get(doc.status or "Draft",set()):frappe.throw(_("Action {0} is not allowed while status is {1}.").format(action,doc.status))
def _source_fingerprint(doc):return payroll_source_fingerprint(frappe,doc.payroll_entry)
def _assert_source_unchanged(doc):
    if not doc.source_fingerprint or doc.source_fingerprint!=_source_fingerprint(doc):frappe.throw(_("Salary Slip source data changed after calculation. Recalculate the allocation."))
def _assert_complete(doc):
    if any(r.severity=="Blocker" and not r.resolved for r in doc.exceptions):frappe.throw(_("Resolve all blocking exceptions first."))
    require_full=True
    if frappe.get_meta("Company").has_field("custom_require_full_payroll_allocation"):
        require_full=bool(frappe.db.get_value("Company",doc.company,"custom_require_full_payroll_allocation"))
    if require_full and abs(flt(doc.allocation_difference))>0.01:frappe.throw(_("Allocation difference must be zero because the Company requires full payroll allocation."))

def _get(run_name,ptype):
    doc=frappe.get_doc("Payroll Allocation Run",run_name);doc.check_permission(ptype);return doc

@frappe.whitelist()
def calculate(run_name):
    doc=_get(run_name,"write")
    if doc.docstatus!=0:frappe.throw(_("Only a draft allocation run can be recalculated."))
    _assert_action(doc,"calculate");calculate_document(doc);doc.save();update_source_status(doc,"Calculated");return doc.as_dict()

@frappe.whitelist()
def approve(run_name):
    doc=_get(run_name,"submit")
    if doc.docstatus!=0:frappe.throw(_("Only a draft allocation run can be approved."))
    _assert_action(doc,"approve");lock_payroll_entry(doc.payroll_entry);_assert_complete(doc);_assert_source_unchanged(doc);reserve_run(doc)
    snapshot,snapshot_hash=build_snapshot(doc);doc.audit_snapshot=snapshot;doc.audit_snapshot_hash=snapshot_hash;doc.engine_version="3.0.2";doc.status="Approved";doc.flags.qorg_approval_submit=True;doc.save();doc.submit();update_source_status(doc,"Approved");return doc.name

@frappe.whitelist()
def post(run_name):
    doc=_get(run_name,"submit")
    if doc.docstatus!=1:frappe.throw(_("Approve and submit the allocation run before posting."))
    _assert_action(doc,"post");lock_payroll_entry(doc.payroll_entry);_assert_complete(doc);_assert_source_unchanged(doc);reserve_run(doc)
    snapshot,snapshot_hash=build_snapshot(doc)
    if doc.audit_snapshot_hash!=snapshot_hash:frappe.throw(_("Approved allocation snapshot changed. Reverse or amend the run."))
    journal=create_reclassification_entry(doc);doc.db_set("journal_entry",journal);doc.db_set("source_accrual_journal_entry",__import__("qorg.qorg.payroll_workforce_allocation.posting",fromlist=["payroll_accrual_journal"]).payroll_accrual_journal(doc));doc.db_set("status","Posted");doc.db_set("posted_by",frappe.session.user);doc.db_set("posted_on",frappe.utils.now_datetime());mark_posted(doc);update_source_status(doc,"Posted");return journal

@frappe.whitelist()
def reconcile(run_name):
    doc=_get(run_name,"read");_assert_action(doc,"reconcile");result=reconcile_run(doc);doc.db_set("reconciliation_status",result["status"]);doc.db_set("liability_reconciliation_status",result["liability_status"]);doc.db_set("payment_reconciliation_status",result["payment_status"]);doc.db_set("reconciled_by",frappe.session.user);doc.db_set("reconciled_on",frappe.utils.now_datetime());doc.save(ignore_permissions=True)
    if result["status"]=="Matched":doc.db_set("status","Reconciled");update_source_status(doc,"Reconciled")
    return result

@frappe.whitelist()
def close(run_name):
    doc=_get(run_name,"submit");_assert_action(doc,"close")
    if doc.reconciliation_status!="Matched":frappe.throw(_("Only a matched allocation run can be closed."))
    doc.db_set("status","Closed");doc.db_set("closed_by",frappe.session.user);doc.db_set("closed_on",frappe.utils.now_datetime());return doc.name

@frappe.whitelist()
def reverse(run_name):
    doc=_get(run_name,"cancel");_assert_action(doc,"reverse");reversal=create_reversal_entry(doc);doc.db_set("reversal_journal_entry",reversal);doc.db_set("status","Reversed");doc.db_set("reconciliation_status","Reversed");release_run(doc,reversed=True);doc.db_set("reversed_by",frappe.session.user);doc.db_set("reversed_on",frappe.utils.now_datetime());update_source_status(doc,"Reversed");return reversal

def submit_run(doc):
    if not getattr(doc.flags,"qorg_approval_submit",False) and doc.status!="Approved":frappe.throw(_("Use Approve Allocation to submit this run."))
    _assert_complete(doc);_assert_source_unchanged(doc)
def cancel_run(doc):
    if doc.status not in {"Reversed","Approved"}:frappe.throw(_("Reverse posted accounting entries before cancelling this run."))
    if doc.journal_entry and not doc.reversal_journal_entry:frappe.throw(_("Create the reversal Journal Entry before cancelling this run."))
    release_run(doc);doc.db_set("status","Cancelled",update_modified=False);update_source_status(doc,"Reversed")
