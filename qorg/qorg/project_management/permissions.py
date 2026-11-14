from __future__ import annotations
import frappe

READ_TYPES={"read","select","print","email","report"}
WRITE_TYPES={"write","create"}
PRIVILEGED_ROLES={"System Manager","Projects Manager"}

def _roles(user): return set(frappe.get_roles(user))
def _privileged(user): return user=="Administrator" or bool(PRIVILEGED_ROLES & _roles(user))
def _employee(user): return frappe.db.get_value("Employee",{"user_id":user,"status":"Active"},"name")

def _assignment(project,user):
    employee=_employee(user)
    if not employee or not project:return None
    return frappe.db.get_value("Project Core Team Assignment",{
        "parent":project,"parenttype":"Project","parentfield":"custom_project_core_team",
        "employee":employee,"active":1,
    },["project_role","can_implement_changes","can_review_changes","can_manage_beneficiaries","can_review_beneficiaries","can_finalize_beneficiaries"],as_dict=True)

def _is_project_manager(project,user):
    if _privileged(user):return True
    employee=_employee(user)
    if not employee:return False
    meta=frappe.get_meta("Project")
    if meta.has_field("custom_project_manager") and frappe.db.get_value("Project",project,"custom_project_manager")==employee:return True
    row=_assignment(project,user)
    return bool(row and row.project_role=="Project Manager")

def _projects(user):
    if _privileged(user):return None
    employee=_employee(user)
    if not employee:return []
    projects=frappe.get_all("Project Core Team Assignment",filters={"employee":employee,"active":1,"parenttype":"Project","parentfield":"custom_project_core_team"},pluck="parent",limit_page_length=0)
    if frappe.get_meta("Project").has_field("custom_project_manager"):
        projects+=frappe.get_all("Project",filters={"custom_project_manager":employee},pluck="name",limit_page_length=0)
    return sorted(set(projects))

def _condition(doctype,user=None):
    projects=_projects(user or frappe.session.user)
    if projects is None:return ""
    if not projects:return "1=0"
    values=", ".join(frappe.db.escape(x) for x in projects)
    return f"`tab{doctype}`.`project` in ({values})"

def _can_write(doc,user):
    project=doc.get("project")
    if _is_project_manager(project,user):return True
    assignment=_assignment(project,user)
    if not assignment:return False
    if doc.doctype=="Project Change Request":
        return bool(assignment.can_implement_changes or assignment.can_review_changes)
    if doc.doctype=="Project Beneficiary Plan":
        return bool(assignment.can_manage_beneficiaries or assignment.can_review_beneficiaries or assignment.can_finalize_beneficiaries)
    employee=_employee(user)
    for fieldname in ("responsible_employee","owner_employee","assigned_to_employee"):
        if doc.meta.has_field(fieldname) and doc.get(fieldname)==employee:return True
    return False

def _has(doc,user=None,permission_type=None):
    user=user or frappe.session.user
    project=doc.get("project")
    projects=_projects(user)
    in_scope=projects is None or project in projects
    if permission_type in READ_TYPES or not permission_type:return in_scope
    if permission_type in WRITE_TYPES:return bool(in_scope and _can_write(doc,user))
    if permission_type in {"submit","cancel","amend","delete","share"}:return bool(in_scope and _is_project_manager(project,user))
    return None

def project_result_query(user=None): return _condition("Project Result",user)
def project_result_has(doc,user=None,permission_type=None): return _has(doc,user,permission_type)
def project_indicator_query(user=None): return _condition("Project Indicator",user)
def project_indicator_has(doc,user=None,permission_type=None): return _has(doc,user,permission_type)
def indicator_target_plan_query(user=None): return _condition("Indicator Target Plan",user)
def indicator_target_plan_has(doc,user=None,permission_type=None): return _has(doc,user,permission_type)
def project_workplan_activity_query(user=None): return _condition("Project Workplan Activity",user)
def project_workplan_activity_has(doc,user=None,permission_type=None): return _has(doc,user,permission_type)
def project_progress_update_query(user=None): return _condition("Project Progress Update",user)
def project_progress_update_has(doc,user=None,permission_type=None): return _has(doc,user,permission_type)
def project_risk_query(user=None): return _condition("Project Risk",user)
def project_risk_has(doc,user=None,permission_type=None): return _has(doc,user,permission_type)
def project_change_request_query(user=None): return _condition("Project Change Request",user)
def project_change_request_has(doc,user=None,permission_type=None): return _has(doc,user,permission_type)
def project_compliance_deliverable_query(user=None): return _condition("Project Compliance Deliverable",user)
def project_compliance_deliverable_has(doc,user=None,permission_type=None): return _has(doc,user,permission_type)
def project_beneficiary_plan_query(user=None): return _condition("Project Beneficiary Plan",user)
def project_beneficiary_plan_has(doc,user=None,permission_type=None): return _has(doc,user,permission_type)
def project_closure_query(user=None): return _condition("Project Closure",user)
def project_closure_has(doc,user=None,permission_type=None): return _has(doc,user,permission_type)
