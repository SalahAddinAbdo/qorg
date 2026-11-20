from __future__ import annotations

import frappe
from frappe.model.document import Document

from qorg.qorg.people_and_opportunities.services.people import (
    update_profile_metrics,
    validate_external_person,
)


class ExternalPerson(Document):
    def validate(self):
        validate_external_person(self)
        update_profile_metrics(self)

    def on_update(self):
        self.db_set("last_profile_update", frappe.utils.now(), update_modified=False)


@frappe.whitelist()
def create_supplier_draft(external_person):
    person=frappe.get_doc("External Person",external_person);person.check_permission("read")
    if person.supplier:return person.supplier
    if not frappe.has_permission("Supplier","create"):frappe.throw("Not permitted to create Supplier.",frappe.PermissionError)
    supplier=frappe.new_doc("Supplier");supplier.supplier_name=person.full_name;supplier.supplier_group=frappe.db.get_single_value("Buying Settings","supplier_group") or frappe.db.get_value("Supplier Group",{"is_group":0},"name");supplier.supplier_type="Individual";supplier.insert()
    person.db_set("supplier",supplier.name,update_modified=False)
    return supplier.name
