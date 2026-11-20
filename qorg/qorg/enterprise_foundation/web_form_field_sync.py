"""Synchronize managed Web Form fields with their source DocField metadata."""

from __future__ import annotations


# Web Form Field does not expose every DocField property on every supported Frappe
# release. Callers pass its runtime meta and this helper copies only supported fields.
MIRRORED_PROPERTIES = (
    "options",
    "description",
    "default",
    "depends_on",
    "mandatory_depends_on",
    "read_only_depends_on",
)


def set_if_supported(row, child_meta, fieldname, value):
    if child_meta.has_field(fieldname):
        row.set(fieldname, value)


def synchronize_web_form_field(row, child_meta, target, definition=None):
    """Copy authoritative field behavior from the source DocField.

    Web forms may be stricter about editability for fields populated by route or
    server context, but they must not invent mandatory rules that differ from the
    source DocType. Conditional properties are mirrored when the installed Web
    Form Field schema supports them.
    """
    definition = definition or {}

    set_if_supported(row, child_meta, "fieldname", target.fieldname)
    set_if_supported(row, child_meta, "fieldtype", target.fieldtype)
    set_if_supported(
        row,
        child_meta,
        "label",
        definition.get("label") or target.label or target.fieldname,
    )

    for property_name in MIRRORED_PROPERTIES:
        set_if_supported(row, child_meta, property_name, getattr(target, property_name, None))

    required = int(bool(getattr(target, "reqd", 0)))
    set_if_supported(row, child_meta, "reqd", required)
    # Older Web Form Field schemas used req. Keep compatibility when available.
    set_if_supported(row, child_meta, "req", required)

    source_read_only = bool(getattr(target, "read_only", 0))
    portal_read_only = bool(definition.get("read_only"))
    set_if_supported(
        row,
        child_meta,
        "read_only",
        int(source_read_only or portal_read_only),
    )

    if target.fieldtype == "Link":
        set_if_supported(row, child_meta, "allow_read_on_all_link_options", 1)
