import frappe
from qorg.qorg.design_system import LOGIN_EXPERIENCE_VERSION
def audit_login_experience():return {"valid":True,"version":LOGIN_EXPERIENCE_VERSION,"site":frappe.local.site}
