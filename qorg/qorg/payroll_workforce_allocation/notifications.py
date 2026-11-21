import frappe
from frappe import _
def _users_for_role(role,company=None):
    users=frappe.get_all("Has Role",filters={"role":role,"parenttype":"User"},pluck="parent",limit_page_length=0);out=[]
    for user in users:
        if company:
            allowed=frappe.get_all("User Permission",filters={"user":user,"allow":"Company"},pluck="for_value",limit_page_length=0)
            if allowed and company not in allowed:continue
        if frappe.db.get_value("User",user,"enabled"):out.append(user)
    return out
def notify_users(subject,message,reference_doctype,reference_name,users):
    for user in sorted(set(x for x in users if x)):
        key=f"{subject}|{reference_doctype}|{reference_name}|{user}"
        if frappe.db.exists("Notification Log",{"for_user":user,"document_type":reference_doctype,"document_name":reference_name,"subject":subject,"read":0}):continue
        frappe.get_doc({"doctype":"Notification Log","subject":subject,"email_content":message,"for_user":user,"document_type":reference_doctype,"document_name":reference_name}).insert(ignore_permissions=True)
def notify_run(run,event):
    roles={"Ready for Approval":["Accounts Manager"],"Posted":["Accounts Manager","Auditor"],"Reconciliation Difference":["Accounts Manager","Payroll Manager"]}.get(event,[]);users=[]
    for role in roles:users+=_users_for_role(role,run.company)
    notify_users(_("Payroll Allocation: {0}").format(event),_("Payroll Allocation Run {0} requires attention.").format(run.name),run.doctype,run.name,users)
def notify_effort(doc,stage):
    users=[]
    if stage=="Employee":users=[frappe.db.get_value("Employee",doc.employee,"user_id")]
    elif stage=="Supervisor":
        supervisor=frappe.db.get_value("Employee",doc.employee,"reports_to");users=[frappe.db.get_value("Employee",supervisor,"user_id")] if supervisor else []
    else:users=_users_for_role("Accounts Manager",doc.company)
    notify_users(_("Monthly Effort Certification pending {0}").format(stage),_("Certification {0} requires your action.").format(doc.name),doc.doctype,doc.name,users)
