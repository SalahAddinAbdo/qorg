from __future__ import annotations
import frappe
from frappe import _
from frappe.utils import cint

def validate_web_form_design_settings(doc, method=None):
    # Global visual settings moved to Q Org Design System Settings.
    return

def apply_managed_design(doc, force=False):
    """Compatibility no-op. Q Org no longer writes generated CSS to Web Form.custom_css."""
    return {"status":"central_design_system","web_form":doc.name or doc.route}

def reconcile_all_web_form_designs(force=False):
    return {"updated":[],"preserved":frappe.get_all("Web Form",pluck="name") if frappe.db.exists("DocType","Web Form") else []}
