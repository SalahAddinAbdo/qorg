from __future__ import annotations
import re
import frappe
from frappe.utils.jinja import render_template

DOC_PATTERN=re.compile(r"(?<!defined\s)\bdoc(?:\.|\[)")

def audit_email_templates():
    results=[]
    for row in frappe.get_all("Email Template",fields=["name","subject","response","response_html"]):
        body=row.response_html or row.response or ""
        item={"name":row.name,"uses_doc":bool(DOC_PATTERN.search(body)),"preview_without_doc":"passed","error":None}
        try:
            render_template(body,{})
        except Exception as exc:
            item["preview_without_doc"]="failed"; item["error"]=str(exc)
        results.append(item)
    return {"total":len(results),"failed":[x for x in results if x["preview_without_doc"]=="failed"],"results":results}
