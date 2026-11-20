from __future__ import annotations
import frappe
from frappe import _
from frappe.utils import flt

def validate_distribution_rows(doc,table_field,source_rows,require_all=False):
    rows=doc.get(table_field) or [];grouped={}
    for row in rows:
        if not row.source_key:frappe.throw(_("Source Key is required at distribution row {0}.").format(row.idx))
        grouped.setdefault(row.source_key,[]).append(row)
        if frappe.db.get_value("Project",row.project,"company") != doc.company:frappe.throw(_("Project at distribution row {0} does not belong to Company.").format(row.idx))
        if row.cost_center and frappe.db.get_value("Cost Center",row.cost_center,"company") != doc.company:frappe.throw(_("Cost Center at distribution row {0} does not belong to Company.").format(row.idx))
        if row.budget_line and frappe.db.get_value("Budget Line",row.budget_line,"project") != row.project:frappe.throw(_("Budget Line at distribution row {0} does not belong to Project.").format(row.idx))
        if row.funding_agreement:
            agreement=frappe.db.get_value("Funding Agreement",row.funding_agreement,["project","docstatus"],as_dict=True) or {}
            if agreement.get("project") and agreement.get("project") != row.project:frappe.throw(_("Funding Agreement at distribution row {0} does not belong to Project.").format(row.idx))
            if agreement.get("docstatus") != 1:frappe.throw(_("Funding Agreement at distribution row {0} must be submitted.").format(row.idx))
        if row.manual_override and not row.override_reason:frappe.throw(_("Override Reason is required at distribution row {0}.").format(row.idx))
    for source_name,source in source_rows.items():
        dist=grouped.get(source_name,[])
        if not dist:
            if require_all:frappe.throw(_("Distribution is required for source row {0}.").format(source.idx))
            continue
        seen=set()
        for row in dist:
            key=(row.project,row.cost_center,row.budget_line,row.funding_agreement,row.donor,row.department)
            if key in seen:frappe.throw(_("Duplicate target dimensions for source row {0}.").format(source.idx))
            seen.add(key)
        total=sum(flt(x.allocated_amount) for x in dist);pct=sum(flt(x.allocation_percentage) for x in dist)
        source_amount=flt(source.get("net_amount") or source.get("amount") or source.get("base_amount"))
        if abs(total-source_amount)>0.01:frappe.throw(_("Distribution for source row {0} must equal {1}. Current total: {2}.").format(source.idx,source_amount,total))
        if abs(pct-100)>0.0001:frappe.throw(_("Distribution percentages for source row {0} must equal 100%. Current total: {1}%.").format(source.idx,pct))
