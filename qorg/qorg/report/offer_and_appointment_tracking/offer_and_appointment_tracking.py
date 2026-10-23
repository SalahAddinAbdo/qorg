import frappe
from frappe import _
def execute(filters=None):
 rows=frappe.get_list("Job Offer",fields=["name","qorg_applicant","applicant_name","offer_date","qorg_valid_until","qorg_response_status","qorg_response_date"],order_by="modified desc")
 cols=[{"label":_("Job Offer"),"fieldname":"name","fieldtype":"Link","options":"Job Offer","width":170,"sticky":True},{"label":_("Applicant"),"fieldname":"qorg_applicant","fieldtype":"Link","options":"Job Applicant","width":190,"sticky":True,"show_title":True},{"label":_("Applicant Name"),"fieldname":"applicant_name","width":200},{"label":_("Offer Date"),"fieldname":"offer_date","fieldtype":"Date","width":110},{"label":_("Valid Until"),"fieldname":"qorg_valid_until","fieldtype":"Date","width":110},{"label":_("Response"),"fieldname":"qorg_response_status","width":110},{"label":_("Response Date"),"fieldname":"qorg_response_date","fieldtype":"Date","width":110}]
 return cols,rows
