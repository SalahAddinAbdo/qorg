import frappe
from frappe import _
from frappe.utils import flt,getdate

def _active(plan,start,end): return [x for x in plan.destinations if (not x.effective_from or getdate(x.effective_from)<=getdate(end)) and (not x.effective_to or getdate(x.effective_to)>=getdate(start))]
def _row(x,share,etype,eref,payload=None): return frappe._dict(project=x.project,cost_center=x.cost_center,funding_agreement=x.funding_agreement,budget_line=x.budget_line,funding_type=x.funding_type,share=flt(share,8),evidence_type=etype,evidence_reference=eref,evidence_payload=frappe.as_json(payload or {}))
def _fixed(plan,start,end): return [_row(x,x.allocation_percentage,"Workforce Funding Plan",plan.name,{"destination_idx":x.idx}) for x in _active(plan,start,end)]
def _timesheet(employee,start,end,allowed):
    rows=frappe.db.sql("""select d.project,sum(d.hours) hours,group_concat(distinct t.name order by t.name) refs from `tabTimesheet Detail` d inner join `tabTimesheet` t on t.name=d.parent where t.docstatus=1 and t.employee=%s and d.from_time>=%s and d.from_time<date_add(%s,interval 1 day) group by d.project""",(employee,start,end),as_dict=True)
    amap={x.project:x for x in allowed};unsupported=[x.project for x in rows if x.project not in amap]
    if unsupported: frappe.throw(_("Submitted Timesheets contain projects not allowed by the plan: {0}").format(", ".join(unsupported)))
    return [(amap[x.project],flt(x.hours),x.refs) for x in rows if flt(x.hours)>0]
def _certified(employee,start,end,allowed):
    names=frappe.get_all("Monthly Effort Certification",filters={"employee":employee,"docstatus":1,"status":"Locked","start_date":["<=",end],"end_date":[">=",start]},pluck="name",limit_page_length=2)
    if len(names)!=1: frappe.throw(_("Exactly one locked Monthly Effort Certification is required for employee {0} and the payroll period.").format(employee))
    doc=frappe.get_doc("Monthly Effort Certification",names[0]);amap={x.project:x for x in allowed};out=[]
    for line in doc.details:
        if line.project not in amap: frappe.throw(_("Certified effort uses project {0}, which is not allowed by the funding plan.").format(line.project))
        out.append(_row(amap[line.project],line.percentage,"Monthly Effort Certification",doc.name,{"row":line.idx,"hours":line.hours,"fingerprint":doc.source_fingerprint}))
    return out
def _compensated(employee,payroll_entry,start,end):
    filters={"employee":employee,"docstatus":1,"start_date":["<=",end],"end_date":[">=",start]};
    if payroll_entry: filters["payroll_entry"]=payroll_entry
    slips=frappe.get_all("Salary Slip",filters=filters,fields=["payment_days","total_working_days","name"],limit_page_length=0)
    days=sum(flt(x.payment_days or x.total_working_days) for x in slips)
    hours=frappe.db.get_value("Employee",employee,"working_hours_per_day") if frappe.get_meta("Employee").has_field("working_hours_per_day") else None
    return days*flt(hours or 8)
def _merge(rows):
    merged={}
    for r in rows:
        key=(r.project,r.cost_center,r.funding_agreement,r.budget_line,r.funding_type); item=merged.setdefault(key,frappe._dict(r,share=0,evidence_payloads=[]));item.share+=flt(r.share);item.evidence_payloads.append({"type":r.evidence_type,"reference":r.evidence_reference,"share":r.share,"payload":r.evidence_payload})
    return [frappe._dict(x,evidence_type="Combined Evidence",evidence_reference="Multiple Sources",evidence_payload=frappe.as_json(x.pop("evidence_payloads"))) for x in merged.values()]
def resolve_effort(plan,employee,start,end,payroll_entry=None):
    allowed=_active(plan,start,end)
    if plan.allocation_method in ("Single Destination","Fixed Percentage"): rows=_fixed(plan,start,end)
    elif plan.allocation_method=="Approved Timesheet":
        actual=_timesheet(employee,start,end,allowed);total=sum(x[1] for x in actual);rows=[_row(x,h/total*100,"Timesheet",refs,{"hours":h}) for x,h,refs in actual] if total else []
    elif plan.allocation_method=="Monthly Certified Effort": rows=_certified(employee,start,end,allowed)
    elif plan.allocation_method=="Hybrid":
        actual=_timesheet(employee,start,end,allowed);comp=_compensated(employee,payroll_entry,start,end);hours=sum(x[1] for x in actual)
        if comp<=0: frappe.throw(_("Compensated hours are unavailable for Hybrid allocation."))
        if hours>comp+0.01: frappe.throw(_("Approved Timesheet hours exceed compensated hours."))
        rows=[_row(x,h/comp*100,"Timesheet",refs,{"hours":h,"compensated_hours":comp}) for x,h,refs in actual];remaining=max(0,100-hours/comp*100);fixed=_fixed(plan,start,end);total=sum(flt(x.share) for x in fixed)
        if remaining and total<=0: frappe.throw(_("Hybrid allocation has a residual percentage but no fixed destinations."))
        rows += [frappe._dict(x,share=remaining*flt(x.share)/total,evidence_type="Funding Plan Residual",evidence_reference=plan.name) for x in fixed] if remaining else []
    else: frappe.throw(_("Unsupported allocation method: {0}").format(plan.allocation_method))
    rows=_merge(rows);total=sum(flt(x.share) for x in rows)
    if rows and abs(total-100)>0.0001: rows[-1].share=flt(rows[-1].share+(100-total),8)
    return rows

@frappe.whitelist()
def certify_effort(name,action):
    doc=frappe.get_doc("Monthly Effort Certification",name);doc.check_permission("write");roles=set(frappe.get_roles())
    expected={"Employee Certify":"Draft","Supervisor Approve":"Employee Certified","Finance Verify":"Supervisor Approved"};target={"Employee Certify":"Employee Certified","Supervisor Approve":"Supervisor Approved","Finance Verify":"Finance Verified"}
    if action not in expected or doc.status!=expected[action]: frappe.throw(_("Invalid certification action."))
    if action=="Employee Certify":
        employee_user=frappe.db.get_value("Employee",doc.employee,"user_id")
        if employee_user!=frappe.session.user and "Payroll Manager" not in roles: frappe.throw(_("Only the employee may certify this effort record."))
    elif action=="Supervisor Approve":
        reports_to=frappe.db.get_value("Employee",doc.employee,"reports_to");supervisor_user=frappe.db.get_value("Employee",reports_to,"user_id") if reports_to else None
        if supervisor_user!=frappe.session.user and not roles.intersection({"HR Manager","Payroll Manager"}): frappe.throw(_("Only the employee supervisor may approve this effort record."))
    elif not roles.intersection({"Accounts Manager","Payroll Manager"}): frappe.throw(_("Only an authorized finance user may verify this effort record."))
    doc.db_set("status",target[action]);return target[action]
