import json
import frappe
from frappe import _
from qorg.qorg.design_system.service import SETTINGS, PRESET, VISUAL_FIELDS, clear_cache, css_variables, effective, update_state, validate_values, values_from

def _manager():
    if frappe.session.user=="Guest" or not frappe.has_permission(SETTINGS,"write"):
        frappe.throw(_("You are not permitted to manage the Q Org Design System."),frappe.PermissionError)

@frappe.whitelist(allow_guest=True)
def get_effective_configuration():
    config = effective()
    if frappe.session.user != "Guest":
        return config
    allowed = ("enabled", "apply_to_login", "apply_to_qorg_web_components", "respect_active_website_theme", "theme_mode_policy", "density", "login_layout", "login_visual_source", "login_visual_image", "login_visual_gradient", "login_welcome_title", "login_welcome_subtitle", "show_login_language_switcher", "login_mobile_visual_policy", "web_form_max_content_width", "web_form_sticky_actions", "web_form_hide_technical_child_row_name", "css_variables")
    return {key: config.get(key) for key in allowed}

@frappe.whitelist(methods=["POST"])
def preview(configuration=None):
    _manager(); values=json.loads(configuration) if isinstance(configuration,str) else (configuration or {})
    doc=frappe.get_single(SETTINGS)
    for k,v in values.items():
        if doc.meta.has_field(k): doc.set(k,v)
    validate_values(doc)
    data={**effective(False),**values}; data["enabled"]=1; data["css_variables"]=css_variables(data)
    return data

@frappe.whitelist(methods=["POST"])
def apply():
    _manager(); doc=frappe.get_single(SETTINGS); doc.save(); clear_cache(); update_state("Managed")
    config=effective(False); frappe.publish_realtime("qorg_design_system_changed",{"fingerprint":config["fingerprint"]},after_commit=True)
    return config

@frappe.whitelist(methods=["POST"])
def restore_frappe_default():
    _manager(); doc=frappe.get_single(SETTINGS); doc.enabled=0; doc.active_preset="Frappe Standard"; doc.save(); clear_cache(); update_state("Restored")
    frappe.publish_realtime("qorg_design_system_changed",{"restored":True},after_commit=True)
    return {"message":_("Frappe Standard appearance restored.")}


@frappe.whitelist(allow_guest=True)
def get_available_languages():
    fields = ["name", "language_name"]
    filters = {"enabled": 1} if frappe.get_meta("Language").has_field("enabled") else {}
    return frappe.get_all("Language", filters=filters, fields=fields, order_by="language_name asc")


@frappe.whitelist(methods=["POST"])
def set_current_user_language(language):
    if frappe.session.user == "Guest":
        frappe.throw(_("Log in before changing the Desk language."), frappe.PermissionError)
    if not frappe.db.exists("Language", language):
        frappe.throw(_("Unknown language: {0}").format(language))
    frappe.db.set_value("User", frappe.session.user, "language", language, update_modified=False)
    frappe.clear_cache(user=frappe.session.user)
    return {"language": language, "reload": True}


@frappe.whitelist(allow_guest=True)
def get_web_form_overrides(route):
    name = frappe.db.get_value("Web Form", {"route": route, "published": 1}, "name")
    if not name:
        return {}
    doc = frappe.get_doc("Web Form", name)
    fields = ("qorg_web_form_design_mode", "qorg_web_form_header_style_override", "qorg_web_form_max_content_width_override", "qorg_web_form_privacy_notice_mode", "qorg_web_form_sticky_actions_mode", "qorg_web_form_child_name_mode")
    return {fieldname: doc.get(fieldname) for fieldname in fields if doc.meta.has_field(fieldname)}


@frappe.whitelist()
def get_quick_create_menu():
    if frappe.session.user == "Guest" or not frappe.db.exists("DocType", SETTINGS):
        return {"enabled": False, "label": _("Create"), "items": []}
    settings = frappe.get_single(SETTINGS)
    if not settings.get("enable_quick_create_menu"):
        return {"enabled": False, "label": _(settings.get("quick_create_button_label")) if settings.get("quick_create_button_label") else _("Create"), "items": []}
    items = []
    rows = sorted(settings.get("quick_create_items") or [], key=lambda row: (row.sequence if row.sequence is not None else 10, row.idx or 0))
    for row in rows:
        doctype = row.reference_doctype
        if not row.enabled or not doctype or not frappe.db.exists("DocType", doctype):
            continue
        meta = frappe.get_meta(doctype)
        if meta.istable or meta.issingle or not frappe.has_permission(doctype, ptype="create"):
            continue
        items.append({
            "doctype": doctype,
            "label": _(row.display_label) if row.display_label else _(doctype),
            "icon": row.icon or "add",
        })
    return {
        "enabled": True,
        "label": _(settings.get("quick_create_button_label")) if settings.get("quick_create_button_label") else _("Create"),
        "items": items,
    }


def _preset_payload(doc):
    return {fieldname: doc.get(fieldname) for fieldname in VISUAL_FIELDS if doc.meta.has_field(fieldname) and doc.get(fieldname) not in (None, "")}


@frappe.whitelist()
def get_preset_configuration(name):
    _manager()
    if not frappe.db.exists(PRESET, name):
        frappe.throw(_("Unknown design preset: {0}").format(name))
    return _preset_payload(frappe.get_doc(PRESET, name))


@frappe.whitelist()
def export_preset(name):
    _manager()
    if not frappe.db.exists(PRESET, name):
        frappe.throw(_("Unknown design preset: {0}").format(name))
    doc = frappe.get_doc(PRESET, name)
    return {"schema_version": doc.schema_version, "preset_name": doc.preset_name, "description": doc.description, "configuration": _preset_payload(doc)}


@frappe.whitelist(methods=["POST"])
def clone_preset(source, target):
    _manager()
    target = (target or "").strip()
    if not target or frappe.db.exists(PRESET, target):
        frappe.throw(_("Enter a unique preset name."))
    source_doc = frappe.get_doc(PRESET, source)
    values = _preset_payload(source_doc)
    doc = frappe.get_doc({"doctype": PRESET, "preset_name": target, "description": _("Cloned from {0}").format(source), "enabled": 1, "is_standard": 0, **values})
    doc.insert()
    return {"name": doc.name}


@frappe.whitelist(methods=["POST"])
def import_preset(payload, target=None):
    _manager()
    if isinstance(payload, str) and len(payload.encode("utf-8")) > 65536:
        frappe.throw(_("Preset JSON cannot exceed 64 KB."))
    try:
        data = json.loads(payload) if isinstance(payload, str) else (payload or {})
    except (TypeError, ValueError):
        frappe.throw(_("The preset JSON is not valid."))
    configuration = data.get("configuration") or {}
    unknown = set(configuration) - set(VISUAL_FIELDS)
    if unknown:
        frappe.throw(_("Unsupported preset keys: {0}").format(", ".join(sorted(unknown))))
    name = (target or data.get("preset_name") or "").strip()
    if not name or frappe.db.exists(PRESET, name):
        frappe.throw(_("Enter a unique preset name."))
    doc = frappe.get_doc({"doctype": PRESET, "preset_name": name, "description": data.get("description") or _("Imported preset"), "enabled": 1, "is_standard": 0, **configuration})
    doc.insert()
    return {"name": doc.name}


@frappe.whitelist()
def validate_current_configuration():
    _manager()
    doc = frappe.get_single(SETTINGS)
    validate_values(doc)
    findings = []
    if doc.get("apply_to_login") and doc.get("login_layout") != "Frappe Standard" and doc.get("login_visual_source") == "Managed Image" and not doc.get("login_visual_image"):
        findings.append({"severity": "Warning", "message": _("Login visual source is Managed Image, but no image is selected.")})
    if doc.get("apply_to_qorg_web_components") and doc.get("respect_active_website_theme") and not doc.get("active_website_theme"):
        findings.append({"severity": "Warning", "message": _("No active Website Theme was detected; Frappe Standard website variables will be used.")})
    if doc.get("enable_quick_create_menu") and not any(row.enabled for row in (doc.get("quick_create_items") or [])):
        findings.append({"severity": "Info", "message": _("The Create button is enabled, but no Create Menu Items are enabled.")})
    return {"valid": not any(row["severity"] in {"Error", "Blocked"} for row in findings), "findings": findings}
