import frappe
from qorg.qorg.design_system import LOGIN_EXPERIENCE_VERSION
from qorg.qorg.design_system.service import SETTINGS, PRESET, BASELINE_PRESET, get_login_configuration

def audit_login_experience():
    checks=[]
    def add(name,passed,detail=None): checks.append({"name":name,"passed":bool(passed),"detail":detail})
    add("Settings exists",frappe.db.exists("DocType",SETTINGS),SETTINGS)
    add("Preset exists",frappe.db.exists("DocType",PRESET),PRESET)
    add("Frappe Standard exists",frappe.db.exists(PRESET,BASELINE_PRESET),BASELINE_PRESET)
    config=get_login_configuration() if checks[0]["passed"] else {}
    add("Login experience enabled",int(config.get("enable_login_experience") or 0)==1,config.get("enable_login_experience"))
    add("Login language switcher enabled",int(config.get("show_login_language_switcher") or 0)==1,config.get("show_login_language_switcher"))
    add("Form title configured",bool(config.get("login_form_title")),config.get("login_form_title"))
    failures=[row for row in checks if not row["passed"]]
    return {"valid":not failures,"checks_total":len(checks),"checks_passed":len(checks)-len(failures),"checks":checks,"version":LOGIN_EXPERIENCE_VERSION,"site":frappe.local.site}
