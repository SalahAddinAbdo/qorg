import json, frappe
from frappe import _

def company_branding(company):
    fields=["company_name","email","custom_print_document_header_color","custom_print_primary_color","custom_print_accent_color","custom_print_light_color","custom_print_border_color"]
    available=[f for f in fields if frappe.get_meta("Company").has_field(f)]
    data=frappe.db.get_value("Company",company,available,as_dict=True) or {}
    return {"company":company,"reply_to":data.get("email"),"header":data.get("custom_print_document_header_color") or "#176b87","primary":data.get("custom_print_primary_color") or "#176b87","accent":data.get("custom_print_accent_color") or "#d8a51d","light":data.get("custom_print_light_color") or "#f6f8fa","border":data.get("custom_print_border_color") or "#dfe3e8"}

def recipients(primary=None, cc=None, additional_users=None, confirm_sender=False):
    out=[]
    for value in [primary]+list(cc or []):
        if value and value not in out: out.append(value)
    for user in additional_users or []:
        email=frappe.db.get_value("User",user,"email") or user
        if email and email not in out: out.append(email)
    if confirm_sender:
        email=frappe.db.get_value("User",frappe.session.user,"email")
        if email and email not in out: out.append(email)
    return out

@frappe.whitelist()
def preview_recruitment_message(template, reference_doctype, reference_name, primary_recipient=None, cc_json=None, users_json=None, confirm_sender=0):
    doc=frappe.get_doc(reference_doctype,reference_name); doc.check_permission("read")
    rec=recipients(primary_recipient,json.loads(cc_json or "[]"),json.loads(users_json or "[]"),bool(int(confirm_sender or 0)))
    if not rec: frappe.throw(_("At least one recipient is required."))
    return {"template":template,"recipients":rec,"reply_to":company_branding(doc.get("company")).get("reply_to"),"reference":f"{reference_doctype}: {reference_name}"}

@frappe.whitelist(methods=["POST"])
def send_recruitment_message(template, reference_doctype, reference_name, primary_recipient=None, cc_json=None, users_json=None, confirm_sender=0):
    preview=preview_recruitment_message(template,reference_doctype,reference_name,primary_recipient,cc_json,users_json,confirm_sender)
    doc=frappe.get_doc(reference_doctype,reference_name); doc.check_permission("read")
    et=frappe.get_doc("Email Template",template); ctx=doc.as_dict(); ctx.update(company_branding(doc.get("company")))
    subject=frappe.render_template(et.subject,ctx); message=frappe.render_template(et.response_html or et.response,ctx)
    frappe.sendmail(recipients=preview["recipients"],subject=subject,message=message,reference_doctype=reference_doctype,reference_name=reference_name,reply_to=preview.get("reply_to"),now=True)
    return preview
