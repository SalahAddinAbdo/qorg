from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt
from frappe.utils.nestedset import NestedSet


from qorg.qorg.project_management.services.project_reconciliation import reconcile_document_projects, reconcile_deleted_document, reconcile_project
class BudgetLine(NestedSet):
    nsm_parent_field = "parent_budget_line"

    def autoname(self):
        self._validate_project()
        self._set_new_code_and_sequence()
        self._normalize_and_validate_code()

        if self.is_group and not self.parent_budget_line:
            self.name = self.project
        else:
            self.name = f"{self.project}-{self.budget_line}"

        if len(self.name) > 140:
            frappe.throw(_("The generated Budget Line ID exceeds 140 characters."))

        if frappe.db.exists(self.doctype, self.name):
            frappe.throw(_("Budget Line ID {0} already exists.").format(frappe.bold(self.name)))

    def before_insert(self):
        self._validate_project()

    def validate(self):
        self._validate_project()
        self._validate_parent()
        self._validate_single_root()
        self._normalize_and_validate_code()
        self._validate_status_and_amount()
        self._protect_locked_values()
        self._set_lock_state()

    def on_update(self):
        self._rollup_project_groups()
        frappe.db.set_value(self.doctype, self.name, "old_parent", self.parent_budget_line or "", update_modified=False)

    def on_trash(self):
        if self.is_group and frappe.db.exists(self.doctype, {"parent_budget_line": self.name}):
            frappe.throw(_("A group Budget Line cannot be deleted while it has child Budget Lines."))

    def after_delete(self):
        self._rollup_project_groups()

    def _validate_project(self):
        if not self.project:
            frappe.throw(_("Project is required."))

    def _validate_single_root(self):
        if self.is_group and not self.parent_budget_line:
            filters = {"project": self.project, "is_group": 1, "parent_budget_line": ["is", "not set"]}
            if self.name:
                filters["name"] = ["!=", self.name]
            if frappe.db.exists(self.doctype, filters):
                frappe.throw(_("Only one root Budget Line is allowed for each Project."))
        elif not self.parent_budget_line:
            frappe.throw(_("Every Budget Line except the Project root must have a Parent Budget Line."))

    def _validate_parent(self):
        if not self.parent_budget_line:
            return
        parent = frappe.db.get_value(self.doctype, self.parent_budget_line,
            ["project", "is_group", "status", "parent_budget_line", "budget_line", "currency"], as_dict=True)
        if not parent:
            frappe.throw(_("Parent Budget Line was not found."))
        if parent.project != self.project:
            frappe.throw(_("Parent Budget Line must belong to the selected Project."))
        if not parent.is_group:
            frappe.throw(_("Parent Budget Line must be a group."))
        if parent.status == "Inactive":
            frappe.throw(_("Inactive Budget Lines cannot be selected as parents."))
        if parent.currency and self.currency and parent.currency != self.currency:
            frappe.throw(_("Budget Line currency must match the parent currency."))

    def _set_new_code_and_sequence(self):
        is_root = self.is_group and not self.parent_budget_line
        if is_root:
            self.sequence = 0
            self.use_custom_code = 0
            self.budget_line = self.project
            return

        if not self.parent_budget_line:
            return

        parent = frappe.db.get_value(
            self.doctype,
            self.parent_budget_line,
            ["parent_budget_line", "budget_line", "currency"],
            as_dict=True,
        )
        if not parent:
            frappe.throw(_("Parent Budget Line was not found."))

        siblings = frappe.get_all(
            self.doctype,
            filters={
                "project": self.project,
                "parent_budget_line": self.parent_budget_line,
            },
            pluck="sequence",
            order_by="sequence desc",
            limit=1,
        )
        self.sequence = int((siblings[0] if siblings else 0) or 0) + 1

        if not self.currency:
            self.currency = parent.currency

        if self.use_custom_code:
            self.budget_line = str(self.budget_line or "").strip()
            if not self.budget_line:
                frappe.throw(_("Budget Line Code is required when Use Donor Code is enabled."))
            return

        if not parent.parent_budget_line:
            self.budget_line = self._alphabetic_sequence(self.sequence)
        else:
            self.budget_line = f"{parent.budget_line}.{self.sequence}"

    @staticmethod
    def _alphabetic_sequence(number):
        number = int(number or 0)
        if number < 1:
            return ""
        letters = []
        while number:
            number, remainder = divmod(number - 1, 26)
            letters.append(chr(65 + remainder))
        return "".join(reversed(letters))

    def _normalize_and_validate_code(self):
        self.budget_line = str(self.budget_line or "").strip()
        if not self.budget_line:
            frappe.throw(_("Budget Line Code is required."))

        filters = {
            "project": self.project,
            "budget_line": self.budget_line,
        }
        if self.name:
            filters["name"] = ["!=", self.name]
        if frappe.db.exists(self.doctype, filters):
            frappe.throw(
                _("Budget Line Code {0} already exists in Project {1}.").format(
                    frappe.bold(self.budget_line), frappe.bold(self.project)
                )
            )

    def _validate_status_and_amount(self):
        if self.status == "Inactive" and self.is_group and frappe.db.exists(self.doctype,
            {"parent_budget_line": self.name, "status": ["!=", "Inactive"]}):
            frappe.throw(_("A group with active child Budget Lines cannot be made Inactive."))
        if flt(self.line_cost) < 0:
            frappe.throw(_("Approved Budget Amount cannot be negative."))
        old_status = self.get_db_value("status") if not self.is_new() else None
        if self.status == "Approved" and old_status != "Approved" and not self.is_group:
            self.original_approved_amount = flt(self.line_cost)

    def _protect_locked_values(self):
        if self.is_new() or not self.get_db_value("budget_line_locked"):
            return
        old = frappe.db.get_value(self.doctype, self.name,
            ["project", "parent_budget_line", "budget_line", "currency", "line_cost", "name1", "status"], as_dict=True)
        if not old:
            return
        changed = [f for f in old if str(old.get(f) or "") != str(self.get(f) or "")]
        if changed and not self._has_active_change_request():
            frappe.throw(_("This approved Budget Line is locked. Use an active Project Change Request."))

    def _has_active_change_request(self):
        if not self.latest_change_request or not frappe.db.exists("DocType", "Project Change Request"):
            return False
        request = frappe.db.get_value("Project Change Request", self.latest_change_request,
            ["docstatus", "implementation_status"], as_dict=True)
        if not request or request.docstatus != 1 or request.implementation_status != "In Progress":
            return False
        if not frappe.db.exists("DocType", "Project Change Affected Item"):
            return False
        return bool(frappe.db.exists("Project Change Affected Item", {
            "parent": self.latest_change_request, "parenttype": "Project Change Request",
            "reference_doctype": self.doctype, "reference_document": self.name,
            "implementation_status": ["in", ["Not Started", "In Progress"]]}))

    def _set_lock_state(self):
        if self.status in ("Approved", "Inactive"):
            self.budget_line_locked = 0 if self._has_active_change_request() else 1
        else:
            self.budget_line_locked = 0

    def _rollup_project_groups(self):
        """Recalculate every group in the Project from the leaves up to the root."""
        if not self.project:
            return

        rows = frappe.get_all(
            self.doctype,
            filters={"project": self.project},
            fields=["name", "parent_budget_line", "is_group", "status", "line_cost"],
            limit_page_length=0,
        )
        if not rows:
            return

        rows_by_name = {row.name: row for row in rows}
        children_by_parent = {}
        for row in rows:
            parent = row.parent_budget_line or ""
            children_by_parent.setdefault(parent, []).append(row)

        totals = {}
        visiting = set()

        def calculate(node_name):
            if node_name in totals:
                return totals[node_name]
            if node_name in visiting:
                frappe.throw(_("A cycle was detected in the Budget Line hierarchy."))

            visiting.add(node_name)
            total = 0.0
            for child in children_by_parent.get(node_name, []):
                if child.status != "Approved":
                    continue
                if child.is_group:
                    total += calculate(child.name)
                else:
                    total += flt(child.line_cost)
            visiting.remove(node_name)
            totals[node_name] = total
            return total

        for row in rows:
            if row.is_group:
                calculate(row.name)

        for name, total in totals.items():
            current = flt(rows_by_name[name].line_cost)
            if current != flt(total):
                frappe.db.set_value(
                    self.doctype,
                    name,
                    "line_cost",
                    total,
                    update_modified=False,
                )



def _qorg_reconcile_on_update(self):
    reconcile_document_projects(self)

def _qorg_reconcile_after_delete(self):
    reconcile_deleted_document(self)

def _qorg_reconcile_on_cancel(self):
    reconcile_document_projects(self)

def _qorg_reconcile_on_update_after_submit(self):
    reconcile_document_projects(self)

_qorg_original_on_update = getattr(BudgetLine, "on_update", None)
def _qorg_wrapped_on_update(self):
    if _qorg_original_on_update:
        _qorg_original_on_update(self)
    reconcile_document_projects(self)
BudgetLine.on_update = _qorg_wrapped_on_update

_qorg_original_after_delete = getattr(BudgetLine, "after_delete", None)
def _qorg_wrapped_after_delete(self):
    if _qorg_original_after_delete:
        _qorg_original_after_delete(self)
    reconcile_deleted_document(self)
BudgetLine.after_delete = _qorg_wrapped_after_delete

_qorg_original_on_cancel = getattr(BudgetLine, "on_cancel", None)
def _qorg_wrapped_on_cancel(self):
    if _qorg_original_on_cancel:
        _qorg_original_on_cancel(self)
    reconcile_document_projects(self)
BudgetLine.on_cancel = _qorg_wrapped_on_cancel

_qorg_original_on_update_after_submit = getattr(BudgetLine, "on_update_after_submit", None)
def _qorg_wrapped_on_update_after_submit(self):
    if _qorg_original_on_update_after_submit:
        _qorg_original_on_update_after_submit(self)
    reconcile_document_projects(self)
BudgetLine.on_update_after_submit = _qorg_wrapped_on_update_after_submit
