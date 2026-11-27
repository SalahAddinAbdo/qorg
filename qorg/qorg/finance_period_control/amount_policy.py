import json
import frappe
from frappe.utils import flt

def _item_tax_map(doc):
    out={}
    for tax in doc.get("taxes") or []:
        raw=tax.get("item_wise_tax_detail")
        if not raw:continue
        try:data=json.loads(raw) if isinstance(raw,str) else raw
        except (TypeError,ValueError):continue
        for key,value in (data or {}).items():
            rate,amount=(value if isinstance(value,(list,tuple)) else (0,value))
            # ERPNext item_wise_tax_detail amounts are transaction currency. Preserve both.
            out.setdefault(str(key),[]).append({"tax":tax,"rate":flt(rate),"transaction_amount":flt(amount)})
    return out

def _nonrecoverable(tax):
    category=(tax.get("category") or "").lower()
    if category in ("valuation","total and valuation"):return True
    if tax.get("included_in_valuation"):return True
    # Only an explicit false value means non-recoverable; missing metadata is not assumed.
    return tax.get("is_recoverable") in (0,"0",False)

def _base_tax(tax):return abs(flt(tax.get("base_tax_amount") if tax.get("base_tax_amount") is not None else tax.get("tax_amount")))
def _base_charge_pool(doc,include_all=False):
    total=0
    for tax in doc.get("taxes") or []:
        if tax.get("charge_type")!="Actual":continue
        if include_all or _nonrecoverable(tax):total+=_base_tax(tax)
    return total

def _discount_pool(doc):return abs(flt(doc.get("base_discount_amount") or 0))
def _weight(doc,row,basis):
    items=doc.get("items") or []
    if basis=="By Quantity":
        den=sum(abs(flt(x.get("qty"))) for x in items);return abs(flt(row.get("qty")))/den if den else 0
    den=sum(abs(flt(x.get("base_net_amount") or x.get("base_amount"))) for x in items)
    return abs(flt(row.get("base_net_amount") or row.get("base_amount")))/den if den else 0

def calculate_row_amount(doc,row,budget_line=None):
    budget_line=budget_line or row.get("budget_line") or row.get("custom_budget_line")
    policy=frappe.db.get_value("Budget Line",budget_line,["commitment_amount_basis","charge_allocation_basis","allow_recoverable_tax"],as_dict=True) if budget_line else frappe._dict()
    basis=policy.get("commitment_amount_basis") or "Net Amount";allocation=policy.get("charge_allocation_basis") or "By Net Amount";rate=flt(doc.get("conversion_rate") or 1)
    net=abs(flt(row.get("base_net_amount") or row.get("base_amount") or row.get("amount")));txn_net=abs(flt(row.get("net_amount") or row.get("amount") or 0))
    eligible_tax=0;all_tax=0;seen=set()
    for key in filter(None,(row.get("item_code"),row.get("name"))):
        for item in _item_tax_map(doc).get(str(key),[]):
            tax=item["tax"];identity=tax.get("name") or id(tax)
            if identity in seen:continue
            base_amount=abs(item["transaction_amount"])*rate;all_tax+=base_amount
            if _nonrecoverable(tax) or policy.get("allow_recoverable_tax"):eligible_tax+=base_amount
            seen.add(identity)
    weight=0 if allocation=="Do Not Allocate" else _weight(doc,row,allocation)
    eligible_charge=_base_charge_pool(doc,False)*weight;all_charge=_base_charge_pool(doc,True)*weight;discount=_discount_pool(doc)*weight
    if basis=="Net Amount":base=net;tax=charge=disc=0
    elif basis=="Net + Non-recoverable Taxes":base=max(net+eligible_tax+eligible_charge-discount,0);tax=eligible_tax;charge=eligible_charge;disc=discount
    elif basis=="Grand Total":base=max(net+all_tax+all_charge-discount,0);tax=all_tax;charge=all_charge;disc=discount
    else:frappe.throw(f"Unsupported commitment amount basis: {basis}")
    txn_amount=base/rate if rate else txn_net
    return {"base_amount":base,"transaction_amount":txn_amount,"transaction_currency":doc.get("currency"),"company_currency":doc.get("company_currency") or frappe.get_cached_value("Company",doc.company,"default_currency"),"conversion_rate":rate,"net_base_amount":net,"tax_base_amount":tax,"charge_base_amount":charge,"discount_base_amount":disc,"amount_policy":f"{basis}; {allocation}"}
