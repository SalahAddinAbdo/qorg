from copy import deepcopy
from collections import defaultdict
import frappe
from frappe import _
from frappe.utils import flt

def split_gl_map(doc, gl_map):
    if not doc.meta.has_field("custom_cost_distributions") or not doc.custom_cost_distributions:return gl_map
    grouped=defaultdict(list)
    for row in doc.custom_cost_distributions:grouped[row.source_row].append(row)
    result=[];matched=set()
    for gle in gl_map:
        detail=gle.get("voucher_detail_no") or gle.get("against_voucher_detail_no");dist=grouped.get(detail)
        if not dist or not eligible(gle):result.append(gle);continue
        matched.add(detail);total=sum(flt(x.allocated_amount) for x in dist)
        remains={f:flt(gle.get(f)) for f in ("debit","credit","debit_in_account_currency","credit_in_account_currency")}
        for idx,target in enumerate(dist):
            row=deepcopy(gle);ratio=flt(target.allocated_amount)/total
            for f in remains:
                val=remains[f] if idx==len(dist)-1 else flt(gle.get(f))*ratio;row[f]=val;remains[f]-=val
            row.update({"project":target.project,"cost_center":target.cost_center})
            for f in ("budget_line","funding_agreement","donor","department"):
                if target.get(f) is not None:row[f]=target.get(f)
            for dim in frappe.get_all("Accounting Dimension",filters={"disabled":0},fields=["fieldname"],limit_page_length=0) if frappe.db.exists("DocType","Accounting Dimension") else []:
                if target.get(dim.fieldname) is not None:row[dim.fieldname]=target.get(dim.fieldname)
            result.append(row)
    missing=set(grouped)-matched
    if missing:frappe.throw(_("No eligible GL row found for distributed source rows: {0}").format(", ".join(sorted(missing))))
    return result

def eligible(gle):
    account=gle.get("account")
    if not account:return False
    values=frappe.db.get_value("Account",account,["root_type","account_type"],as_dict=True) or {}
    return values.get("root_type")=="Expense" and values.get("account_type") not in ("Tax","Stock","Fixed Asset","Bank","Cash","Receivable","Payable","Round Off","Temporary")
