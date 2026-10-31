import re,frappe
SETTINGS="Q Org Design System Settings"
def get_ui_tokens():
 d=frappe.get_single(SETTINGS);r=max(0,min(32,int(d.get("border_radius") or 4)))
 def c(v,f):return v.upper() if isinstance(v,str) and re.fullmatch(r"#[0-9A-Fa-f]{6}",v.strip()) else f
 return {"primary_color":c(d.get("primary_color"),"#137690"),"secondary_color":c(d.get("secondary_color"),"#CBAE66"),"border_radius":r}
def get_login_configuration():
 d=frappe.get_single(SETTINGS);names=["enable_login_experience","show_login_language_switcher","login_background_image","login_background_position","login_overlay_strength","login_text_color","login_visual_title","login_visual_subtitle","login_form_title","login_form_subtitle","login_brand_logo","login_footer_text"];return {n:d.get(n) for n in names if d.meta.has_field(n)}
