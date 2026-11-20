from __future__ import annotations
import inspect
import frappe
from frappe import _

REQUIRED_DOCTYPES=(
 "Cost Distribution Profile","Cost Distribution Profile Target","Cost Distribution Transaction Type",
 "Cost Distribution Row","Cost Distribution Ledger","Service and Allowance Accrual",
)
SOURCE_CHILDREN=("Material Request Item","Supplier Quotation Item","Purchase Order Item","Purchase Invoice Item","Expense Claim Detail","Stock Entry Detail","Service and Allowance Accrual Line")
TRANSACTION_FIELDS=(
 "custom_cost_distribution_section","custom_cost_distributions","custom_distribution_status","custom_distribution_hash",
)
TRANSACTIONS=("Material Request","Supplier Quotation","Purchase Order","Purchase Invoice","Expense Claim","Stock Entry")

@frappe.whitelist()
def audit_runtime_configuration():
    checks=[]
    def add(name,passed,details=None,severity="Error"):
        checks.append({"check":name,"passed":bool(passed),"severity":severity,"details":details or ""})
    for dt in REQUIRED_DOCTYPES:
        add(f"DocType: {dt}",frappe.db.exists("DocType",dt),frappe.db.get_value("DocType",dt,["module","custom","istable","is_submittable"],as_dict=True))
    for child in SOURCE_CHILDREN:
        if frappe.db.exists("DocType",child):add(f"Source key: {child}",frappe.get_meta(child,cached=False).get_field("custom_distribution_source_key") is not None)
    for dt in TRANSACTIONS:
        meta=frappe.get_meta(dt,cached=False)
        for fieldname in TRANSACTION_FIELDS:
            df=meta.get_field(fieldname);add(f"{dt}.{fieldname}",df is not None,{"fieldtype":getattr(df,"fieldtype",None),"insert_after":getattr(df,"insert_after",None),"options":getattr(df,"options",None)})
        table=meta.get_field("custom_cost_distributions")
        add(f"{dt} distribution table options",table and table.options=="Cost Distribution Row",getattr(table,"options",None))
    for dt in frappe.get_all("DocType",filters={"istable":1,"module":"QOrg"},pluck="name"):
        nested=[df.fieldname for df in frappe.get_meta(dt,cached=False).fields if df.fieldtype=="Table"]
        add(f"No nested table: {dt}",not nested,nested)
    accrual_line=frappe.get_meta("Service and Allowance Accrual Line",cached=False)
    accrual=frappe.get_meta("Service and Allowance Accrual",cached=False)
    add("Nested accrual field removed",accrual_line.get_field("cost_distribution") is None)
    add("Accrual head distribution table",bool(accrual.get_field("cost_distributions")),getattr(accrual.get_field("cost_distributions"),"options",None))
    row_meta=frappe.get_meta("Cost Distribution Row",cached=False)
    add("Distribution grid maximum eight columns",len([x for x in row_meta.fields if x.in_list_view]) <= 8,[x.fieldname for x in row_meta.fields if x.in_list_view])
    profile_meta=frappe.get_meta("Cost Distribution Profile",cached=False)
    method_field=profile_meta.get_field("distribution_method")
    add("Only implemented methods exposed",set((method_field.options or "").split("\n")) <= {"Fixed Percentage","Fixed Amount","Equal Distribution"},method_field.options)
    add("Purchase Invoice class extension",_hook_contains("extend_doctype_class","Purchase Invoice","PurchaseInvoiceCostDistributionMixin"))
    add("Expense Claim class extension",_hook_contains("extend_doctype_class","Expense Claim","ExpenseClaimCostDistributionMixin"))
    for dt in TRANSACTIONS+("Service and Allowance Accrual",):
        for event in ("before_validate","before_submit","on_submit","on_cancel"):
            add(f"Hook {dt}.{event}",_event_hook_contains(dt,event,"qorg.qorg.cost_distribution.adapters.common"))
    try:
        from erpnext.accounts.doctype.purchase_invoice.purchase_invoice import PurchaseInvoice
        add("Purchase Invoice get_gl_entries signature","warehouse_account" in inspect.signature(PurchaseInvoice.get_gl_entries).parameters,str(inspect.signature(PurchaseInvoice.get_gl_entries)))
    except Exception as exc:add("Purchase Invoice controller import",False,repr(exc))
    try:
        from erpnext.accounts.doctype.expense_claim.expense_claim import ExpenseClaim
        add("Expense Claim get_gl_entries exists",hasattr(ExpenseClaim,"get_gl_entries"),str(inspect.signature(ExpenseClaim.get_gl_entries)) if hasattr(ExpenseClaim,"get_gl_entries") else "")
    except Exception as exc:add("Expense Claim controller import",False,repr(exc))
    dimension_fields=[]
    if frappe.db.exists("DocType","Accounting Dimension"):
        dimension_fields=frappe.get_all("Accounting Dimension",filters={"disabled":0},pluck="fieldname")
    dimension_row_meta=frappe.get_meta("Cost Distribution Row",cached=False)
    for fieldname in dimension_fields:add(f"Dynamic dimension: {fieldname}",dimension_row_meta.get_field(fieldname) is not None)
    failed=[x for x in checks if not x["passed"] and x["severity"]=="Error"]
    return {"passed":not failed,"summary":{"total":len(checks),"passed":len(checks)-len(failed),"failed":len(failed)},"checks":checks}

def _hook_contains(hook,doctype,needle):
    value=frappe.get_hooks(hook).get(doctype,[]) if isinstance(frappe.get_hooks(hook),dict) else []
    if isinstance(value,str):value=[value]
    return any(needle in x for x in value)

def _event_hook_contains(doctype,event,needle):
    hooks=frappe.get_hooks("doc_events") or {};value=(hooks.get(doctype) or {}).get(event,[])
    if isinstance(value,str):value=[value]
    return any(needle in x for x in value)
