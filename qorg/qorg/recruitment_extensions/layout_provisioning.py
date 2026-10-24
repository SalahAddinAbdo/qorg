import json
import frappe


def _load_layouts():
    path=frappe.get_app_path("qorg","qorg","recruitment_extensions","data","form_layouts.json")
    return json.load(open(path,encoding="utf-8"))


def _field_exists(doctype,fieldname):
    return frappe.get_meta(doctype).has_field(fieldname)


def _first_anchor(doctype,candidates):
    meta=frappe.get_meta(doctype)
    for fieldname in candidates:
        if meta.has_field(fieldname): return fieldname
    standard=[field.fieldname for field in meta.fields if not field.get("is_custom_field") and field.fieldtype not in ("Tab Break",)]
    return standard[-1] if standard else ""


def reconcile_recruitment_form_layouts():
    layouts=_load_layouts()
    for doctype,plan in layouts.items():
        if not frappe.db.exists("DocType",doctype): continue
        frappe.clear_cache(doctype=doctype)
        previous=_first_anchor(doctype,plan.get("anchors") or [])
        sequence=900
        for definition in plan.get("fields") or []:
            fieldname=definition["fieldname"]
            name=f"{doctype}-{fieldname}"
            if not frappe.db.exists("Custom Field",name):
                continue
            values={"insert_after":previous,"idx":sequence}
            if definition.get("label") is not None: values["label"]=definition.get("label")
            frappe.db.set_value("Custom Field",name,values,update_modified=False)
            previous=fieldname;sequence+=1
        frappe.clear_cache(doctype=doctype)


@frappe.whitelist()
def repair_recruitment_form_layouts():
    if frappe.session.user!="Administrator": frappe.throw("Administrator only",frappe.PermissionError)
    reconcile_recruitment_form_layouts()
    return {"ok":True,"message":"Recruitment form layouts reconciled."}
