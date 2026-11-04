from __future__ import annotations

from contextlib import contextmanager

import frappe
from frappe import _
from frappe.model.document import Document

_INTERNAL_FLAG = "qorg_managed_configuration_state_write"


def is_internal_managed_state_write() -> bool:
    return bool(getattr(frappe.flags, _INTERNAL_FLAG, False))


@contextmanager
def managed_state_write():
    previous = getattr(frappe.flags, _INTERNAL_FLAG, False)
    setattr(frappe.flags, _INTERNAL_FLAG, True)
    try:
        yield
    finally:
        setattr(frappe.flags, _INTERNAL_FLAG, previous)


class ManagedConfigurationState(Document):
    """Internal state owned and updated only by Q Org policy services."""

    def before_insert(self):
        self._validate_internal_write()

    def validate(self):
        self._validate_internal_write()

    def on_trash(self):
        self._validate_internal_write()

    def _validate_internal_write(self):
        if not is_internal_managed_state_write():
            frappe.throw(
                _(
                    "Managed Configuration State is maintained internally by Q Org and cannot be changed manually."
                ),
                frappe.PermissionError,
            )
