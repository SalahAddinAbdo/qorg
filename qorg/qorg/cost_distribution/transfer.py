from __future__ import annotations
import frappe

def copy_distribution(source,target,source_row_map=None,source_field="custom_cost_distributions",target_field="custom_cost_distributions"):
    source_row_map=source_row_map or {}
    target.set(target_field,[])
    for row in source.get(source_field) or []:
        values=row.as_dict(no_nulls=True);values.pop("name",None);values.pop("idx",None);values.pop("parent",None);values.pop("parenttype",None);values.pop("parentfield",None);values.pop("doctype",None)
        values["source_row"]=source_row_map.get(row.source_row,row.source_row)
        values["distribution_source"]="Transferred"
        target.append(target_field,values)
