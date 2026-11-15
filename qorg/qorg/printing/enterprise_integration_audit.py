from __future__ import annotations
import frappe
from qorg.qorg.printing.jinja_audit import audit_email_templates

def audit_enterprise_forms():
    result={"doctypes":0,"child_doctypes":0,"link_fields":0,"page_break":[],"email_templates":audit_email_templates()}
    for row in frappe.get_all("DocType",filters={"custom":0},fields=["name","module","istable"]):
        meta=frappe.get_meta(row.name); result["doctypes"]+=1; result["child_doctypes"]+=int(row.istable or 0)
        if row.istable:
            df=meta.get_field("page_break"); result["page_break"].append({"doctype":row.name,"module":row.module,"exists":bool(df),"fieldtype":getattr(df,"fieldtype",None),"allow_on_submit":getattr(df,"allow_on_submit",None),"print_hide":getattr(df,"print_hide",None)})
        result["link_fields"]+=sum(1 for df in meta.fields if df.fieldtype=="Link")
    result["page_break_missing"]=[x for x in result["page_break"] if not x["exists"]]
    result["page_break_invalid"]=[x for x in result["page_break"] if x["exists"] and (x["fieldtype"]!="Check" or not x["allow_on_submit"] or not x["print_hide"])]
    result["passed"]=not result["page_break_missing"] and not result["page_break_invalid"] and not result["email_templates"]["failed"]
    return result
