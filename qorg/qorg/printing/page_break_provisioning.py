from __future__ import annotations
import frappe
from qorg.qorg.enterprise_foundation.idempotent_provisioning import create_custom_fields_if_changed

EXCLUDED_MODULES={"Core","Desk","Workflow","Email","Printing","Integrations","Data Migration","Custom"}
EXCLUDED_NAMES={"Dynamic Link","DocType Link","DocType Action","Workflow Document State","Workflow Transition","Notification Recipient","Email Template","Custom Field"}

def _eligible_child_doctypes():
    rows=frappe.get_all("DocType",filters={"istable":1,"custom":0},fields=["name","module"])
    return sorted(row.name for row in rows if row.name not in EXCLUDED_NAMES and row.module not in EXCLUDED_MODULES)

def provision_printable_child_row_page_breaks():
    result={"created_or_updated":[],"adopted":[],"excluded":[],"conflicts":[]}
    definition={"fieldname":"page_break","label":"Page Break After This Row","fieldtype":"Check","default":"0","allow_on_submit":1,"print_hide":1,"in_list_view":0,"in_standard_filter":0,"is_system_generated":1,"module":"QOrg","description":"Starts a new printed page after this row when supported by the selected print format."}
    for doctype in _eligible_child_doctypes():
        meta=frappe.get_meta(doctype)
        existing=meta.get_field("page_break")
        if existing and existing.fieldtype!="Check":
            result["conflicts"].append({"doctype":doctype,"fieldtype":existing.fieldtype}); continue
        if existing and not frappe.db.exists("Custom Field",f"{doctype}-page_break"):
            result["adopted"].append(doctype); continue
        create_custom_fields_if_changed({doctype:[definition]},update=True)
        result["created_or_updated"].append(doctype)
    return result
