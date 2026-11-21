import frappe
PRIVILEGED={"System Manager","Payroll Manager","Accounts Manager"}
READ_ONLY={"Auditor"}
AGGREGATE_ROLES={"Grant Manager","Projects Manager"}
def _roles(user=None):return set(frappe.get_roles(user or frappe.session.user))
def _employee(user):return frappe.db.get_value("Employee",{"user_id":user},"name")
def _companies(user,doctype=None):
    return frappe.get_all("User Permission",filters={"user":user,"allow":"Company","applicable_for":["in",[None,"",doctype]]},pluck="for_value",limit_page_length=0)
def _company_condition(dt,user):
    companies=_companies(user,dt)
    return "" if not companies else f"`tab{dt}`.`company` in ({','.join(frappe.db.escape(x) for x in companies)})"
def payroll_run_query(user=None):
    user=user or frappe.session.user;roles=_roles(user)
    if roles&PRIVILEGED or roles&READ_ONLY:return ""
    if roles&({"HR Manager"}|AGGREGATE_ROLES):return _company_condition("Payroll Allocation Run",user)
    return "1=0"
def plan_query(user=None):
    user=user or frappe.session.user;roles=_roles(user)
    if roles&(PRIVILEGED|{"HR Manager"}|READ_ONLY):return ""
    employee=_employee(user);return f"`tabWorkforce Funding Plan`.`employee`={frappe.db.escape(employee)}" if employee else "1=0"
def policy_query(user=None):
    user=user or frappe.session.user;roles=_roles(user)
    if roles&(PRIVILEGED|{"HR Manager","Grant Manager"}|READ_ONLY):return _company_condition("Payroll Cost Policy",user) if not roles&PRIVILEGED else ""
    return "1=0"
def effort_query(user=None):
    user=user or frappe.session.user;roles=_roles(user)
    if roles&(PRIVILEGED|{"HR Manager","Projects Manager"}|READ_ONLY):return _company_condition("Monthly Effort Certification",user) if not roles&PRIVILEGED else ""
    employee=_employee(user);return f"`tabMonthly Effort Certification`.`employee`={frappe.db.escape(employee)}" if employee else "1=0"
def has_payroll_run_permission(doc,ptype="read",user=None):
    user=user or frappe.session.user;roles=_roles(user)
    if roles&PRIVILEGED:return True
    if roles&READ_ONLY:return ptype in {"read","report","export","print"}
    if roles&({"HR Manager"}|AGGREGATE_ROLES):return ptype in {"read","report","print"} and (not _companies(user,"Payroll Allocation Run") or doc.company in _companies(user,"Payroll Allocation Run"))
    return False
def has_plan_permission(doc,ptype="read",user=None):
    user=user or frappe.session.user;roles=_roles(user)
    if roles&(PRIVILEGED|{"HR Manager"}):return True
    if roles&READ_ONLY:return ptype in {"read","report","export","print"}
    return bool(_employee(user)==doc.employee and ptype in {"read","print"})
def has_policy_permission(doc,ptype="read",user=None):
    roles=_roles(user);return True if roles&PRIVILEGED else ptype in {"read","report","print"} and bool(roles&({"HR Manager","Grant Manager","Auditor"}))
def has_effort_permission(doc,ptype="read",user=None):
    user=user or frappe.session.user;roles=_roles(user)
    if roles&PRIVILEGED:return True
    if roles&READ_ONLY:return ptype in {"read","report","export","print"}
    if _employee(user)==doc.employee:return ptype in {"read","write","print"} and doc.docstatus==0
    if "HR Manager" in roles:return True
    if "Projects Manager" in roles:return ptype in {"read","report","print"}
    return False
def can_view_employee_amounts(user=None):return bool(_roles(user)&(PRIVILEGED|{"HR Manager","Auditor"}))
def can_view_funding_amounts(user=None):return bool(_roles(user)&(PRIVILEGED|{"Grant Manager","Auditor"}))
def assert_report_access(aggregate=False):
    roles=_roles()
    allowed=PRIVILEGED|READ_ONLY|{"HR Manager","Grant Manager","Projects Manager"}
    if not roles&allowed:frappe.throw("Not permitted to access payroll reports.",frappe.PermissionError)
    return {"employee_amounts":can_view_employee_amounts(),"funding_amounts":can_view_funding_amounts(),"aggregate_only":aggregate or bool(roles&AGGREGATE_ROLES and not roles&PRIVILEGED)}
