import frappe
from qorg.qorg.design_system.service import SETTINGS
def provision_login_experience():
 if not frappe.db.exists("DocType",SETTINGS):return
 d=frappe.get_single(SETTINGS);defs={"primary_color":"#137690","secondary_color":"#CBAE66","border_radius":4,"show_language_action":1,"enable_login_experience":1,"show_login_language_switcher":1,"login_background_position":"Center","login_overlay_strength":"Medium","login_text_color":"Light","login_visual_title":"Q Org","login_visual_subtitle":"Integrated enterprise management for your organization.","login_form_title":"Welcome","login_form_subtitle":"Sign in to continue"};changed=False
 for f,v in defs.items():
  if d.meta.has_field(f) and d.get(f) in (None,""):d.set(f,v);changed=True
 if changed:d.flags.ignore_permissions=True;d.save()
