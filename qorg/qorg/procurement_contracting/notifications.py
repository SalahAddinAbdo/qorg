import frappe

TEMPLATES = [
    ("QOrg Procurement - Approved Purchase Request", "Approved purchase request {{ doc.name }}", "An approved purchase request requires your action. Method: {{ doc.custom_procurement_method or '' }}. Next action: {{ doc.custom_procurement_next_action or '' }}."),
    ("QOrg Procurement - Committee Assignment", "Procurement committee assignment for {{ doc.procurement_process }}", "You have been assigned to a procurement committee. Open the process, complete the confidentiality and conflict declaration, and act before the due date."),
    ("QOrg Procurement - Technical Evaluation Due", "Technical evaluation due for {{ doc.procurement_process }}", "Your technical evaluation is pending. Please complete and submit the assigned evaluation before the deadline."),
    ("QOrg Procurement - Financial Evaluation Opened", "Financial evaluation opened for {{ doc.procurement_process }}", "The technical stage has been approved and the financial evaluation is now open to the assigned financial committee."),
    ("QOrg Procurement - Award Decision Required", "Award decision required for {{ doc.procurement_process }}", "The main committee recommendation is ready for authorized award decision."),
    ("QOrg Procurement - Receipt or Acceptance Required", "Receipt or acceptance required for {{ doc.purchase_order }}", "A delivery or contractual milestone requires receipt, inspection, or technical acceptance before invoicing."),
    ("QOrg Procurement - Supplier Registration Received", "Supplier registration received", "Your supplier registration has been received and will be reviewed. Reference: {{ doc.name }}."),
    ("QOrg Procurement - Bid Submission Received", "Bid submission received", "Your bid has been received successfully. Reference: {{ doc.name }}. Submission time: {{ doc.submitted_at }}."),
    ("QOrg Procurement - Awarded", "Procurement award notification", "Your submission has been selected. The contracting team will contact the authorized supplier representative with the next steps."),
    ("QOrg Procurement - Not Selected", "Procurement result notification", "Thank you for participating. Your submission was not selected for this procurement process."),
]


def provision_email_templates():
    for name, subject, response in TEMPLATES:
        if frappe.db.exists("Email Template", name):
            continue
        frappe.get_doc({
            "doctype": "Email Template",
            "name": name,
            "subject": subject,
            "response_html": f"<div style='font-family:Arial,sans-serif;line-height:1.6'><p>{response}</p><p>{{{{ _(\"This is an automated procurement notification.\") }}}}</p></div>",
            "use_html": 1,
        }).insert(ignore_permissions=True)
NOTIFICATIONS=[
 ("QOrg - Approved Purchase Request Assigned","Material Request","doc.docstatus == 1 and doc.material_request_type == 'Purchase'","Approved Purchase Request","custom_current_responsible_user"),
 ("QOrg - Award Decision Required","Award Recommendation","doc.docstatus == 1","Award Decision Required","owner"),
 ("QOrg - Contract Expiry Reminder","Procurement Contract","doc.status == 'Active'","Contract Expiry Reminder","contract_manager"),
]
def provision_notifications():
 for name,doctype,condition,subject,receiver_field in NOTIFICATIONS:
  if frappe.db.exists("Notification",name): continue
  doc=frappe.get_doc({"doctype":"Notification","name":name,"subject":subject,"document_type":doctype,"event":"Save","condition":condition,"channel":"Email","message":"{{ doc.name }} - {{ doc.status or doc.workflow_state or '' }}","enabled":1})
  doc.append("recipients",{"receiver_by_document_field":receiver_field})
  doc.insert(ignore_permissions=True)
