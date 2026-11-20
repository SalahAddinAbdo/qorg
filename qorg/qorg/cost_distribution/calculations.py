from frappe import _
import frappe
from frappe.utils import flt
def calculate_targets(profile,amount,base_amount=None):
 targets=[x for x in profile.targets if x.allow_distribution]
 if not targets:return []
 if profile.distribution_method not in ("Fixed Percentage","Fixed Amount","Equal Distribution"):frappe.throw(_("Distribution Method {0} is not implemented.").format(profile.distribution_method))
 amount=flt(amount);base_amount=flt(base_amount if base_amount is not None else amount);rows=[];remaining=amount;base_remaining=base_amount
 if profile.distribution_method=="Fixed Amount" and sum(flt(x.fixed_amount) for x in targets)>amount+0.01:frappe.throw(_("Fixed target amounts exceed the source amount."))
 for idx,target in enumerate(targets):
  if profile.distribution_method=="Fixed Percentage":ratio=flt(target.allocation_percentage)/100;value=amount*ratio;base=base_amount*ratio
  elif profile.distribution_method=="Fixed Amount":value=flt(target.fixed_amount);base=value*(base_amount/amount if amount else 1)
  else:value=amount/len(targets);base=base_amount/len(targets)
  if target.maximum_amount and value>flt(target.maximum_amount):frappe.throw(_("Target row {0} exceeds Maximum Amount.").format(target.idx))
  if idx==len(targets)-1 and profile.difference_handling=="Allocate Rounding Difference":value=remaining;base=base_remaining
  value=round(value,2);base=round(base,2);remaining=round(remaining-value,2);base_remaining=round(base_remaining-base,2);rows.append({"target":target,"allocated_amount":value,"base_amount":base})
 if profile.require_full_distribution and abs(sum(x["allocated_amount"] for x in rows)-amount)>0.01:frappe.throw(_("Full distribution is required."))
 return rows
