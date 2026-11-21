import frappe
from frappe import _
from frappe.utils import flt

def precision(currency):
    value = frappe.db.get_value("Currency", currency, "fraction_units") if currency and frappe.db.exists("Currency", currency) else None
    return 2 if value in (None, 0) else len(str(int(value))) - 1

def company_currency(company):
    return frappe.get_cached_value("Company", company, "default_currency")

def exchange_rate(from_currency, to_currency, posting_date):
    if not from_currency or not to_currency or from_currency == to_currency:
        return 1.0
    try:
        from erpnext.setup.utils import get_exchange_rate
        rate = get_exchange_rate(from_currency, to_currency, posting_date)
    except Exception:
        rate = None
    if not rate:
        frappe.throw(_("Exchange rate from {0} to {1} is missing for {2}.").format(from_currency, to_currency, posting_date))
    return flt(rate)

def convert(amount, from_currency, to_currency, posting_date):
    rate = exchange_rate(from_currency, to_currency, posting_date)
    return flt(flt(amount) * rate, precision(to_currency)), rate
