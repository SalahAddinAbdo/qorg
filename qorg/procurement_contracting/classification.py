import frappe
from frappe import _

def resolve_procurement_type(items):
    kinds=set()
    for row in items:
        if not row.item_code:
            kinds.add(getattr(row,"custom_non_stock_procurement_type",None) or "Goods")
            continue
        item=frappe.get_cached_doc("Item",row.item_code)
        if item.is_stock_item or item.is_fixed_asset:
            kinds.add("Goods")
        else:
            kinds.add(getattr(row,"custom_non_stock_procurement_type",None) or "Services")
    kinds.discard(None)
    if not kinds: return "Goods"
    return next(iter(kinds)) if len(kinds)==1 else "Mixed"
