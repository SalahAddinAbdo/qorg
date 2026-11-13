import frappe
from frappe.utils import add_days, nowdate, get_url_to_form


def _sent_today(reference_doctype, reference_name, subject):
    return bool(frappe.db.exists("Email Queue", {
        "reference_doctype": reference_doctype,
        "reference_name": reference_name,
        "subject": subject,
        "creation": [">=", nowdate()],
    }))


def send_inventory_reminders():
    days = int(frappe.db.get_single_value("Stock Settings", "custom_custody_reminder_days") or 7)
    records = frappe.get_all(
        "Asset Custody",
        filters={
            "docstatus": 1,
            "custody_status": ["in", ["Active", "Return Due", "Overdue"]],
            "expected_return_date": ["<=", add_days(nowdate(), days)],
        },
        fields=["name", "custodian"],
    )
    template = frappe.get_doc("Email Template", "Custody Return Reminder")
    for row in records:
        email = (
            frappe.db.get_value("Employee", row.custodian, "company_email")
            or frappe.db.get_value("Employee", row.custodian, "personal_email")
        )
        if not email:
            continue
        context = {"name": row.name, "record_url": get_url_to_form("Asset Custody", row.name)}
        subject = frappe.render_template(template.subject, context)
        if _sent_today("Asset Custody", row.name, subject):
            continue
        frappe.sendmail(
            recipients=[email],
            subject=subject,
            message=frappe.render_template(template.response_html, context),
            reference_doctype="Asset Custody",
            reference_name=row.name,
        )
