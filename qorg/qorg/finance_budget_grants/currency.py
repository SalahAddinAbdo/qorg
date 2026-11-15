from __future__ import annotations
import frappe
from frappe import _
from frappe.utils import flt, getdate, nowdate

RATE_TYPES = ("Agreement Fixed", "Transaction Date", "Manual Approved")

def company_currency(company: str) -> str:
    currency = frappe.db.get_value("Company", company, "default_currency")
    if not currency:
        frappe.throw(_("Default currency is required for company {0}.").format(company))
    return currency

def exchange_rate(from_currency: str, to_currency: str, date=None, rate_type="Transaction Date", manual_rate=None) -> float:
    if not from_currency or not to_currency:
        frappe.throw(_("Both source and target currencies are required."))
    if from_currency == to_currency:
        return 1.0
    if rate_type == "Manual Approved":
        rate = flt(manual_rate)
    else:
        from erpnext.setup.utils import get_exchange_rate
        rate = flt(get_exchange_rate(from_currency, to_currency, getdate(date or nowdate()), args="for_buying"))
    if rate <= 0:
        frappe.throw(_("A positive exchange rate is required for {0} to {1}.").format(from_currency, to_currency))
    return rate

def convert(amount, rate) -> float:
    return flt(amount) * flt(rate)

def validate_agreement_currency(doc):
    base = company_currency(doc.company)
    rate_type = doc.get("exchange_rate_type") or "Agreement Fixed"
    if rate_type not in RATE_TYPES:
        frappe.throw(_("Invalid exchange rate type."))
    if doc.agreement_currency == base:
        doc.exchange_rate = 1
    elif rate_type == "Transaction Date":
        doc.exchange_rate = exchange_rate(doc.agreement_currency, base, doc.get("exchange_rate_date") or doc.start_date)
    elif flt(doc.exchange_rate) <= 0:
        frappe.throw(_("Exchange Rate must be greater than zero."))
    doc.base_amount = convert(doc.agreement_amount, doc.exchange_rate)
    if not doc.get("exchange_rate_date"):
        doc.exchange_rate_date = doc.start_date or nowdate()
    if not doc.get("exchange_rate_source"):
        doc.exchange_rate_source = "ERPNext Currency Exchange" if rate_type == "Transaction Date" else rate_type
