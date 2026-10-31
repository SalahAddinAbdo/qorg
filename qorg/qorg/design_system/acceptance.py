from __future__ import annotations
import frappe
from qorg.qorg.design_system import THEME_SCHEMA_VERSION
from qorg.qorg.design_system.service import CACHE_KEY, DEFAULTS, PRESET, SETTINGS, effective
REQUIRED_PRESETS=("Frappe Standard","Q Org Enterprise","Q Org Compact","Q Org Dark","Q Org Accessible")
REQUIRED_ASSETS=("qorg_theme.bundle.js","qorg_theme.bundle.scss","qorg_theme_admin.bundle.js","qorg_theme_web.bundle.js","qorg_theme_web.bundle.scss")
def audit_runtime_configuration():
 checks=[]
 def add(name,passed,detail=None,severity="Error"): checks.append({"name":name,"passed":bool(passed),"detail":detail,"severity":severity})
 add("Settings DocType exists",bool(frappe.db.exists("DocType",SETTINGS)),SETTINGS)
 add("Preset DocType exists",bool(frappe.db.exists("DocType",PRESET)),PRESET)
 if not all(x["passed"] for x in checks): return _finish(checks)
 config=effective(False)
 add("Schema version",config.get("schema_version")==THEME_SCHEMA_VERSION,config.get("schema_version"))
 add("Cache key",CACHE_KEY=="qorg:theme:effective:v3.1.3",CACHE_KEY)
 add("Small configuration contract",len(DEFAULTS)<=20,len(DEFAULTS))
 add("Effective fields complete",not [x for x in DEFAULTS if x not in config],[x for x in DEFAULTS if x not in config])
 add("Semantic tokens generated",len(config.get("tokens") or {})>=12,len(config.get("tokens") or {}))
 for name in REQUIRED_PRESETS: add(f"Preset: {name}",bool(frappe.db.exists(PRESET,name)),name)
 settings=frappe.get_single(SETTINGS)
 duplicates=[]; seen=set()
 for row in settings.get("quick_create_items") or []:
  if row.reference_doctype in seen: duplicates.append(row.reference_doctype)
  seen.add(row.reference_doctype)
 add("Quick Create unique",not duplicates,duplicates)
 report=_finish(checks); report.update({"schema_version":THEME_SCHEMA_VERSION,"site":frappe.local.site,"active_preset":config.get("active_preset"),"fingerprint":config.get("fingerprint"),"required_assets":REQUIRED_ASSETS}); return report
def _finish(checks):
 failures=[x for x in checks if not x["passed"] and x["severity"] in {"Error","Blocked"}]
 return {"valid":not failures,"checks_total":len(checks),"checks_passed":sum(x["passed"] for x in checks),"checks_failed":len(failures),"checks":checks}
