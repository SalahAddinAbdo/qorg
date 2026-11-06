import frappe

def _is_manager(user):
    roles=set(frappe.get_roles(user)); return bool({"Administrator","System Manager","Procurement Manager"} & roles)

def _assigned(process_name, fieldname, user):
    mandate=frappe.db.get_value("Procurement Process",process_name,fieldname)
    if not mandate: return False
    return bool(frappe.db.exists("Procurement Committee Member",{"parent":mandate,"parenttype":"Procurement Committee Mandate","user":user,"active":1,"recused":0}))

def submission_has_permission(doc,user=None,permission_type=None):
    user=user or frappe.session.user
    if _is_manager(user): return True
    return doc.owner==user

def technical_evaluation_has_permission(doc,user=None,permission_type=None):
    user=user or frappe.session.user
    return _is_manager(user) or _assigned(doc.procurement_process,"technical_committee",user)

def financial_evaluation_has_permission(doc,user=None,permission_type=None):
    user=user or frappe.session.user
    if _is_manager(user): return True
    if not _assigned(doc.procurement_process,"financial_committee",user): return False
    status=frappe.db.get_value("Procurement Process",doc.procurement_process,"status")
    return status in ("Technical Evaluation Approved","Financial Evaluation In Progress","Financial Evaluation Approved","Combined Evaluation Completed","Recommendation Submitted","Award Approved","Closed")

def technical_query(user):
    if _is_manager(user): return ""
    u=frappe.db.escape(user)
    return f"exists (select 1 from `tabProcurement Process` p join `tabProcurement Committee Member` m on m.parent=p.technical_committee and m.parenttype='Procurement Committee Mandate' where p.name=`tabProcurement Technical Evaluation`.procurement_process and m.user={u} and m.active=1 and ifnull(m.recused,0)=0)"

def financial_query(user):
    if _is_manager(user): return ""
    u=frappe.db.escape(user)
    return f"exists (select 1 from `tabProcurement Process` p join `tabProcurement Committee Member` m on m.parent=p.financial_committee and m.parenttype='Procurement Committee Mandate' where p.name=`tabProcurement Financial Evaluation`.procurement_process and m.user={u} and m.active=1 and ifnull(m.recused,0)=0)"
