from __future__ import annotations
import frappe
from frappe import _
from frappe.utils import flt
from .actuals import get_posted_actual
from .commitments import get_open_commitments

def snapshot(budget_line):
    line=frappe.db.get_value("Budget Line",budget_line,["name","project","line_cost","original_approved_amount","allow_budget_transfer","flexibility_percent","funding_agreement","currency"],as_dict=True)
    if not line: frappe.throw(_("Budget Line {0} does not exist.").format(budget_line))
    actual=get_posted_actual(project=line.project,budget_line=line.name)
    commitment=get_open_commitments(project=line.project,budget_line=line.name)["open_commitment"]
    approved=flt(line.line_cost)
    return {**line,"approved_budget":approved,"posted_actual":actual,"open_commitment":commitment,"available_balance":approved-actual-commitment,"utilization_percent":(actual+commitment)*100/approved if approved else 0}

def validate_available_budget(budget_line,additional_amount=0):
    data=snapshot(budget_line); projected=flt(data["posted_actual"])+flt(data["open_commitment"])+flt(additional_amount)
    allowed=flt(data["approved_budget"])
    if projected>allowed:
        frappe.throw(_("Budget Line {0} would be exceeded by {1}. Approved: {2}; actual and commitments after this transaction: {3}.").format(budget_line,projected-allowed,allowed,projected))
    return data
