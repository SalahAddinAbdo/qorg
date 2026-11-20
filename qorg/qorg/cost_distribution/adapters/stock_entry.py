import frappe
from frappe import _
from frappe.utils import flt
SUPPORTED=("Material Issue","Material Transfer")
def prepare_stock_rows(doc):
    if doc.purpose not in SUPPORTED or not doc.get("custom_cost_distributions"):return
    grouped={}
    for row in doc.custom_cost_distributions:grouped.setdefault(row.source_row,[]).append(row)
    originals={r.name:r for r in doc.items};generated=[];consumed=set()
    for name,dist in grouped.items():
        source=originals.get(name)
        if not source:frappe.throw(_("Stock source row {0} was not found.").format(name))
        if source.serial_and_batch_bundle or source.serial_no or source.batch_no:frappe.throw(_("Split serialized or batched stock rows explicitly using standard Stock Entry rows."))
        if abs(sum(flt(x.allocated_quantity) for x in dist)-flt(source.qty))>0.000001:frappe.throw(_("Allocated quantity must equal source quantity at row {0}.").format(source.idx))
        for target in dist:
            values=source.as_dict(no_nulls=True)
            for f in ("name","idx","parent","parentfield","parenttype","doctype"):values.pop(f,None)
            values.update({"qty":target.allocated_quantity,"transfer_qty":flt(target.allocated_quantity)*flt(source.conversion_factor or 1),"project":target.project,"cost_center":target.cost_center});generated.append(values)
        consumed.add(name)
    kept=[r.as_dict(no_nulls=True) for r in doc.items if r.name not in consumed];doc.set("items",[])
    for values in kept+generated:
        for f in ("name","idx","parent","parentfield","parenttype","doctype"):values.pop(f,None)
        doc.append("items",values)
