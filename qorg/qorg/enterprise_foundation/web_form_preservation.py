"""Preservation policy for application-provisioned Web Forms."""

from __future__ import annotations


def preserve_existing_web_form(doc, managed_version=None):
    """Mark an existing form for review without overwriting user configuration.

    Existing fields, order, labels, required/read-only flags, conditions, scripts,
    CSS, and form settings remain untouched. The application definition is used
    only when creating a missing Web Form. Administrators can then merge a new
    managed definition deliberately instead of losing local configuration during
    migrate or upgrade.
    """
    if doc.meta.has_field("qorg_managed_update_available"):
        doc.qorg_managed_update_available = 1
    if managed_version and doc.meta.has_field("qorg_managed_version") and not doc.qorg_managed_version:
        # Record the first observed application version only; never rewrite an
        # administrator's existing management metadata.
        doc.qorg_managed_version = managed_version
    return "preserved"
