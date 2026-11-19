from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
import frappe
from frappe import _
from frappe.utils import flt, getdate, now_datetime

@dataclass(frozen=True)
class CurrencyResult:
    from_currency:str
    to_currency:str
    rate:float
    rate_type:str
    rate_date:object
    source:str
    precision:int
    manual_approval_reference:str|None=None

def company_currency(company:str)->str:
    currency=frappe.get_cached_value("Company",company,"default_currency")
    if not currency:frappe.throw(_("Company {0} does not have a default currency.").format(company))
    return currency

def currency_precision(currency=None,company=None,default=2)->int:
    precision=frappe.db.get_single_value("System Settings","currency_precision") or frappe.db.get_default("currency_precision") or default
    if currency and frappe.db.exists("Currency",currency):
        number_format=frappe.db.get_value("Currency",currency,"number_format") or ""
        decimal_part=number_format.rsplit(".",1)[1] if "." in number_format else ""
        digits=sum(1 for char in decimal_part if char in ("0","#"))
        if digits: precision=digits
    return max(0,min(int(precision),9))

def quantize(amount,precision=2):
    step=Decimal(1).scaleb(-int(precision));return float(Decimal(str(amount or 0)).quantize(step,rounding=ROUND_HALF_UP))

def resolve_exchange_rate(from_currency:str,to_currency:str,date=None,rate_type="Transaction Date",manual_rate=None,manual_approval_reference=None,rate_source=None)->CurrencyResult:
    date=getdate(date or frappe.utils.nowdate());precision=currency_precision(to_currency)
    if not from_currency or not to_currency:frappe.throw(_("From Currency and To Currency are required."))
    if from_currency==to_currency:return CurrencyResult(from_currency,to_currency,1.0,"Same Currency",date,"Identity",precision)
    if rate_type in ("Agreement Fixed","Manual Approved"):
        rate=flt(manual_rate)
        if rate<=0:frappe.throw(_("A positive approved exchange rate is required for {0}.").format(rate_type))
        if rate_type=="Manual Approved" and not manual_approval_reference:frappe.throw(_("Manual Rate Approval Reference is required."))
        return CurrencyResult(from_currency,to_currency,rate,rate_type,date,rate_source or rate_type,precision,manual_approval_reference)
    direct=frappe.db.get_value("Currency Exchange",{"from_currency":from_currency,"to_currency":to_currency,"date":["<=",date]},["exchange_rate","date","name"],as_dict=True,order_by="date desc")
    if direct and flt(direct.exchange_rate)>0:return CurrencyResult(from_currency,to_currency,flt(direct.exchange_rate),"Transaction Date",direct.date,f"Currency Exchange {direct.name}",precision)
    inverse=frappe.db.get_value("Currency Exchange",{"from_currency":to_currency,"to_currency":from_currency,"date":["<=",date]},["exchange_rate","date","name"],as_dict=True,order_by="date desc")
    if inverse and flt(inverse.exchange_rate)>0:return CurrencyResult(from_currency,to_currency,1/flt(inverse.exchange_rate),"Transaction Date",inverse.date,f"Inverse Currency Exchange {inverse.name}",precision)
    frappe.throw(_("No Currency Exchange rate exists from {0} to {1} on or before {2}. Create a rate or use an approved manual rate.").format(from_currency,to_currency,date))

def exchange_rate(from_currency:str,to_currency:str,date=None,rate_type="Transaction Date",manual_rate=None,manual_approval_reference=None,rate_source=None)->float:
    return resolve_exchange_rate(from_currency,to_currency,date,rate_type,manual_rate,manual_approval_reference,rate_source).rate

def convert(amount,rate,precision=2)->float:return quantize(flt(amount)*flt(rate),precision)

def convert_between(amount,from_currency,to_currency,date=None,rate_type="Transaction Date",manual_rate=None,manual_approval_reference=None,rate_source=None):
    result=resolve_exchange_rate(from_currency,to_currency,date,rate_type,manual_rate,manual_approval_reference,rate_source);return convert(amount,result.rate,result.precision),result

def validate_agreement_currency(doc):
    base=company_currency(doc.company);doc.currency_precision=doc.currency_precision or currency_precision(doc.agreement_currency,doc.company)
    result=resolve_exchange_rate(doc.agreement_currency,base,doc.exchange_rate_date or doc.start_date,doc.exchange_rate_type,doc.exchange_rate,doc.manual_rate_approval_reference,doc.exchange_rate_source)
    doc.exchange_rate=result.rate;doc.exchange_rate_date=result.rate_date;doc.exchange_rate_source=result.source;doc.base_amount=convert(doc.agreement_amount,result.rate,currency_precision(base,doc.company))
    if doc.docstatus==1:doc.exchange_rate_locked=1
    return result

def append_exchange_audit(doc,result,context="Agreement Currency"):
    if not doc.meta.has_field("exchange_rate_audit"):return
    exists=any(r.from_currency==result.from_currency and r.to_currency==result.to_currency and flt(r.rate)==flt(result.rate) and str(r.rate_date)==str(result.rate_date) for r in doc.exchange_rate_audit)
    if exists:return
    doc.append("exchange_rate_audit",{"conversion_context":context,"from_currency":result.from_currency,"to_currency":result.to_currency,"rate":result.rate,"rate_type":result.rate_type,"rate_date":result.rate_date,"rate_source":result.source,"manual_approval_reference":result.manual_approval_reference,"reference_doctype":doc.doctype,"reference_name":doc.name,"locked_on":now_datetime(),"locked_by":frappe.session.user})

def prevent_locked_rate_change(doc):
    if doc.is_new() or not doc.get("exchange_rate_locked"):return
    old=doc.get_doc_before_save()
    if not old:return
    fields=("agreement_currency","exchange_rate","exchange_rate_type","exchange_rate_date","exchange_rate_source","manual_rate_approval_reference")
    changed=[f for f in fields if str(old.get(f) or "")!=str(doc.get(f) or "")]
    if changed:frappe.throw(_("Submitted exchange-rate evidence is locked. Amend the Funding Agreement instead of changing: {0}.").format(", ".join(changed)))
