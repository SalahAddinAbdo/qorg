from __future__ import annotations
from frappe import _

import frappe
from frappe.desk.query_report import get_report_doc as core_get_report_doc
from frappe.desk.query_report import run as core_run

from qorg.qorg.enterprise_foundation.interface_policy_engine import (
    is_interface_allowed,
)


def _check(report_name: str | None) -> None:
    if report_name and not is_interface_allowed("Report", report_name):
        frappe.throw(
            _("Report {0} is not available.").format(report_name),
            frappe.PermissionError,
        )


@frappe.whitelist()
def get_report_doc(report_name: str, **kwargs):
    _check(report_name)
    return core_get_report_doc(report_name=report_name, **kwargs)


@frappe.whitelist()
def run(report_name: str, **kwargs):
    _check(report_name)
    return core_run(report_name=report_name, **kwargs)
