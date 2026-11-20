from __future__ import annotations
import frappe
from frappe import _
from frappe.utils import getdate

SPECIFICITY={"Item":100,"Item Group":90,"Expense Type":80,"Expense Account":70,"Procurement Category":60,"Department":50,"Cost Center":40,"Transaction Type":20,"Company Default":10}

def resolve_profile(*,company,posting_date,doctype,item=None,item_group=None,expense_type=None,expense_account=None,procurement_category=None,department=None,cost_center=None,subtype=None):
    if not company or not posting_date or not doctype:return None
    rows=frappe.get_all("Cost Distribution Profile",filters={"company":company,"status":"Active","docstatus":1,"effective_from":["<=",posting_date]},fields=["name","priority","match_basis","effective_from","effective_to"],limit_page_length=0)
    matches=[]
    values={"Item":item,"Item Group":item_group,"Expense Type":expense_type,"Expense Account":expense_account,"Procurement Category":procurement_category,"Department":department,"Cost Center":cost_center}
    for row in rows:
        if row.effective_to and getdate(row.effective_to)<getdate(posting_date):continue
        profile=frappe.get_cached_doc("Cost Distribution Profile",row.name)
        if not any(t.active and t.document_type==doctype and (not t.transaction_subtype or t.transaction_subtype==subtype) for t in profile.transaction_types):continue
        if row.match_basis not in ("Transaction Type","Company Default") and profile.get(frappe.scrub(row.match_basis)) != values.get(row.match_basis):continue
        matches.append((row.priority,SPECIFICITY.get(row.match_basis,0),getdate(row.effective_from),row.name))
    if not matches:return None
    matches.sort(reverse=True);best=matches[0]
    ties=[x for x in matches if x[:3]==best[:3]]
    if len(ties)>1:frappe.throw(_("Conflicting Cost Distribution Profiles: {0}").format(", ".join(x[3] for x in ties)))
    return frappe.get_doc("Cost Distribution Profile",best[3])
