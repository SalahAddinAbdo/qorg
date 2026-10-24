import json
import frappe
def reconcile_participation_layouts():
    path=frappe.get_app_path("qorg","qorg","volunteer_management","data","form_layouts.json")
    plans=json.load(open(path,encoding="utf-8"))
    for dt,fields in plans.items():
        previous="";idx=900
        for field in fields:
            name=f"{dt}-{field}"
            if not frappe.db.exists("Custom Field",name):continue
            frappe.db.set_value("Custom Field",name,{"insert_after":previous,"idx":idx},update_modified=False);previous=field;idx+=1
        frappe.clear_cache(doctype=dt)
