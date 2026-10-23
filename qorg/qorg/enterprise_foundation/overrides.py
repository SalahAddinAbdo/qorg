from __future__ import annotations

from frappe.model.rename_doc import update_document_title as core_update_document_title

from qorg.qorg.enterprise_foundation.policy_enforcement import enforce_rename_policy


def update_document_title(
    *,
    doctype: str,
    docname: str,
    title: str | None = None,
    name: str | None = None,
    merge: bool = False,
    enqueue: bool = False,
    **kwargs,
) -> str:
    enforce_rename_policy(doctype)
    return core_update_document_title(
        doctype=doctype,
        docname=docname,
        title=title,
        name=name,
        merge=merge,
        enqueue=enqueue,
        **kwargs,
    )
