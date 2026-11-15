import frappe
def execute(filters=None):
 cols=[{"label":"Project Closure","fieldname":"name","fieldtype":"Link","options":"Project Closure","width":160},{"label":"Project","fieldname":"project","fieldtype":"Link","options":"Project","width":180},{"label":"Open Commitments","fieldname":"open_commitments_amount","fieldtype":"Currency","width":130},{"label":"Unsettled Advances","fieldname":"unsettled_advances_amount","fieldtype":"Currency","width":130},{"label":"Financial Closeout","fieldname":"financial_closeout_completed","fieldtype":"Check","width":120},{"label":"Grant Closeout","fieldname":"grant_closeout_completed","fieldtype":"Check","width":120}]
 return cols,frappe.get_all("Project Closure",fields=[c["fieldname"] for c in cols],order_by="modified desc")
