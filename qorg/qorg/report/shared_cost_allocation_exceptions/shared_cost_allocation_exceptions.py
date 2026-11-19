import frappe
from frappe import _
from frappe.utils import flt
from qorg.qorg.shared_cost_allocation.reporting import in_selected,apply_view,chart_by,summary

def execute(filters=None):
 f=frappe._dict(filters or {});runs=frappe.get_all("Shared Cost Allocation Run",filters={"company":f.company,"posting_date":["between",[f.from_date,f.to_date]]},fields=["name","posting_date","allocation_category","run_type","run_status"]);rows=[]
 for run in runs:
  for e in frappe.get_all("Shared Cost Allocation Entry",filters={"parent":run.name,"eligibility_status":["!=","Eligible"]},fields=["project","donor","funding_agreement","budget_line","source_voucher_type","source_voucher","source_account","allocated_amount","eligibility_status","exception_message"]):
   if not in_selected(e.project,f,"project") or not in_selected(e.donor,f,"donor") or not in_selected(e.funding_agreement,f,"funding_agreement") or not in_selected(e.eligibility_status,f,"eligibility_status"):continue
   rows.append({"run":run.name,**run,**e})
 columns=[{"label":_("Run"),"fieldname":"run","fieldtype":"Link","options":"Shared Cost Allocation Run","width":160,"sticky":1},{"label":_("Project"),"fieldname":"project","fieldtype":"Link","options":"Project","width":160,"sticky":1},{"label":_("Date"),"fieldname":"posting_date","fieldtype":"Date","width":95},{"label":_("Category"),"fieldname":"allocation_category","width":145},{"label":_("Donor"),"fieldname":"donor","fieldtype":"Link","options":"Donor","width":145},{"label":_("Funding Agreement"),"fieldname":"funding_agreement","fieldtype":"Link","options":"Funding Agreement","width":175},{"label":_("Budget Line"),"fieldname":"budget_line","fieldtype":"Link","options":"Budget Line","width":160},{"label":_("Source Voucher"),"fieldname":"source_voucher","fieldtype":"Dynamic Link","options":"source_voucher_type","width":150},{"label":_("Source Account"),"fieldname":"source_account","fieldtype":"Link","options":"Account","width":170},{"label":_("Amount"),"fieldname":"allocated_amount","fieldtype":"Currency","width":110},{"label":_("Status"),"fieldname":"eligibility_status","width":95},{"label":_("Exception"),"fieldname":"exception_message","width":300}]
 amount=sum(flt(x.allocated_amount) for x in rows)
 return apply_view(columns,f.view_mode),rows,None,chart_by(rows,"project","allocated_amount",_("Exception Amount")),summary([(_("Exceptions"),len(rows),"Int","Red" if rows else "Green"),(_("Affected Amount"),amount,"Currency","Orange"),(_("Projects"),len(set(x.project for x in rows)),"Int","Blue")]),1
