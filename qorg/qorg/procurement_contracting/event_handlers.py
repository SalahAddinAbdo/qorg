import frappe
from qorg.qorg.procurement_contracting.communications import send_template

STATUS_MAP={
 "Opening Completed":("opening_committee","Bid Opening Completed"),
 "Setup Approved":("technical_committee","Technical Evaluation Assignment"),
 "Technical Evaluation Approved":("financial_committee","Financial Evaluation Ready"),
}
def notify_assigned_committee(doc,method=None):
 if not doc.has_value_changed("status") or doc.status not in STATUS_MAP:return
 field,template=STATUS_MAP[doc.status];committee=doc.get(field)
 if not committee:return
 users=frappe.get_all("Committee Member",filters={"parent":committee,"parenttype":"Procure Committee","active":1,"recused":0},pluck="user")
 recipients=[frappe.db.get_value("User",u,"email") or u for u in users]
 recipients=[x for x in recipients if x]
 if recipients:send_template(doc.doctype,doc.name,template,recipients)
