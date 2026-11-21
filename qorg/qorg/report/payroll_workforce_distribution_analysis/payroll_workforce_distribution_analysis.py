import json
from collections import defaultdict

import frappe
from frappe import _
from frappe.utils import flt, getdate

from qorg.qorg.payroll_workforce_allocation.permissions import assert_report_access


def execute(filters=None):
    filters = frappe._dict(filters or {})
    access = assert_report_access(aggregate=filters.get("view_mode") in ("Project Summary", "Funding Agreement Summary", "Donor Summary", "Donor Statement"))
    validate_filters(filters)
    if access.get("aggregate_only") and filters.get("view_mode") in ("Employee with Project Details", "Employee Totals Only", "Government Payroll Register", "Audit Review", "Salary Component Analysis"):
        filters.view_mode = "Project Summary"
    slips = get_salary_slips(filters)
    if not slips:
        return get_columns(filters, [], access), [], _("No Salary Slips match the selected filters and document status."), None, get_summary([], filters)

    slip_names = [row.name for row in slips]
    allocations = get_allocations(filters, slip_names)
    components = get_salary_components(filters, slip_names)
    donor_map = get_donor_map({row.funding_agreement for row in allocations if row.funding_agreement})
    source_rows = build_rows(slips, allocations, components, donor_map, filters, access)
    rows = apply_view(source_rows, filters, access)
    columns = get_columns(filters, components, access)
    chart = get_chart(rows, filters)
    summary = get_summary(source_rows, filters)
    message = get_message(filters, access)
    return columns, rows, message, chart, summary, 1


@frappe.whitelist()
def get_donor_options(txt=None):
    assert_report_access(aggregate=True)
    meta = frappe.get_meta("Funding Agreement")
    field = next((name for name in ("donor", "primary_donor", "funding_source") if meta.has_field(name)), None)
    if not field:
        return []
    filters = {field: ["like", f"%{txt or ''}%"]} if txt else {}
    values = frappe.get_all("Funding Agreement", filters=filters, pluck=field, distinct=True, limit_page_length=50)
    return [{"value": value, "description": value} for value in values if value]


def validate_filters(filters):
    if not filters.get("company"):
        frappe.throw(_("Company is required."))
    if not filters.get("from_date") or not filters.get("to_date"):
        frappe.throw(_("From Date and To Date are required."))
    if getdate(filters.from_date) > getdate(filters.to_date):
        frappe.throw(_("From Date cannot be later than To Date."))


def as_list(value):
    if not value:
        return []
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return [x for x in parsed if x]
        except Exception:
            return [value]
    return list(value) if isinstance(value, (list, tuple, set)) else [value]


def get_salary_slips(filters):
    slip_status = filters.get("salary_slip_status") or "Submitted"
    status_map = {"Draft": 0, "Submitted": 1, "Draft and Submitted": ["in", [0, 1]], "All": ["in", [0, 1, 2]]}
    where = {"company": filters.company, "docstatus": status_map.get(slip_status, 1)}
    basis = filters.get("period_basis") or "Period Overlap"
    if basis == "Posting Date":
        where["posting_date"] = ["between", [filters.from_date, filters.to_date]]
    elif basis == "End Date":
        where["end_date"] = ["between", [filters.from_date, filters.to_date]]
    elif basis == "Fully Within Period":
        where["start_date"] = [">=", filters.from_date]
        where["end_date"] = ["<=", filters.to_date]
    else:
        where["end_date"] = [">=", filters.from_date]
        where["start_date"] = ["<=", filters.to_date]
    for field in ("employee", "payroll_entry"):
        values = as_list(filters.get(field))
        if values:
            where[field] = ["in", values]
    slips = frappe.get_all("Salary Slip", filters=where, fields=[
        "name", "employee", "employee_name", "company", "start_date", "end_date", "posting_date",
        "payroll_entry", "gross_pay", "total_deduction", "net_pay", "currency", "exchange_rate", "docstatus"
    ], order_by="employee asc,end_date asc,name asc", limit_page_length=0)
    employee_names = {x.employee for x in slips}
    employees = {x.name: x for x in frappe.get_all("Employee", filters={"name": ["in", list(employee_names)]}, fields=["name", "department", "branch", "designation"], limit_page_length=0)} if employee_names else {}
    for slip in slips:
        employee = employees.get(slip.employee) or frappe._dict()
        slip.department = employee.get("department")
        slip.branch = employee.get("branch")
        slip.designation = employee.get("designation")
    for field in ("department", "branch", "designation"):
        values = set(as_list(filters.get(field)))
        if values:
            slips = [row for row in slips if row.get(field) in values]
    return slips


def get_allocations(filters, slip_names):
    run_filters = {"docstatus": 1, "company": filters.company}
    status = filters.get("allocation_status") or "Posted and Reconciled"
    status_map = {
        "All Active": ["in", ["Approved", "Posted", "Reconciled", "Closed", "Reversed"]],
        "Posted and Reconciled": ["in", ["Posted", "Reconciled", "Closed"]],
    }
    if status in status_map:
        run_filters["status"] = status_map[status]
    elif status != "All Active":
        run_filters["status"] = status
    run_names = frappe.get_all("Payroll Allocation Run", filters=run_filters, pluck="name", limit_page_length=0)
    if not run_names:
        return []
    where = {"parent": ["in", run_names], "parenttype": "Payroll Allocation Run", "docstatus": 1, "salary_slip": ["in", slip_names]}
    for field in ("project", "funding_agreement", "budget_line", "salary_component"):
        values = as_list(filters.get(field))
        if values:
            where[field] = ["in", values]
    rows = frappe.get_all("Payroll Allocation Result", filters=where, fields=[
        "parent as allocation_run", "salary_slip", "employee", "salary_component", "component_category",
        "component_amount", "work_share", "eligible_percentage", "allocated_amount", "ineligible_amount",
        "company_currency_amount", "currency", "project", "cost_center", "funding_agreement", "budget_line",
        "funding_type", "evidence_type", "evidence_reference"
    ], limit_page_length=0)
    minimum = flt(filters.get("minimum_amount"))
    if minimum:
        rows = [row for row in rows if abs(flt(row.company_currency_amount or row.allocated_amount)) >= minimum]
    return rows


def get_salary_components(filters, slip_names):
    where = {"parent": ["in", slip_names], "parenttype": "Salary Slip", "parentfield": ["in", ["earnings", "deductions"]]}
    selected = as_list(filters.get("salary_component"))
    if selected:
        where["salary_component"] = ["in", selected]
    component_type = filters.get("component_type")
    if component_type == "Earning":
        where["parentfield"] = "earnings"
    elif component_type == "Deduction":
        where["parentfield"] = "deductions"
    rows = frappe.get_all("Salary Detail", filters=where, fields=["parent", "parentfield", "salary_component", "amount", "idx"], order_by="parentfield asc,idx asc", limit_page_length=0)
    order = {}
    for row in rows:
        key = (row.parentfield, row.salary_component)
        order[key] = min(order.get(key, row.idx), row.idx)
    return sorted(order, key=lambda key: (0 if key[0] == "earnings" else 1, order[key], key[1]))


def get_donor_map(agreements):
    if not agreements:
        return {}
    meta = frappe.get_meta("Funding Agreement")
    donor_field = next((field for field in ("donor", "primary_donor", "funding_source") if meta.has_field(field)), None)
    if not donor_field:
        return {name: None for name in agreements}
    rows = frappe.get_all("Funding Agreement", filters={"name": ["in", list(agreements)]}, fields=["name", donor_field], limit_page_length=0)
    return {row.name: row.get(donor_field) for row in rows}


def build_rows(slips, allocations, components, donor_map, filters, access):
    allocation_by_slip = defaultdict(list)
    for item in allocations:
        item.donor = donor_map.get(item.funding_agreement)
        allocation_by_slip[item.salary_slip].append(item)

    selected_donors = set(as_list(filters.get("donor")))
    if selected_donors:
        allocation_by_slip = defaultdict(list, {
            name: [item for item in items if item.donor in selected_donors]
            for name, items in allocation_by_slip.items()
        })

    allocation_scope = any(as_list(filters.get(field)) for field in (
        "project", "funding_agreement", "donor", "budget_line", "salary_component"
    )) or bool(filters.get("component_type")) or bool(flt(filters.get("minimum_amount")))
    percentage_basis = filters.get("percentage_basis") or "Selected Scope (100%)"

    salary_component_map = defaultdict(float)
    detail_rows = frappe.get_all("Salary Detail", filters={
        "parent": ["in", [x.name for x in slips]], "parenttype": "Salary Slip",
        "parentfield": ["in", ["earnings", "deductions"]]
    }, fields=["parent", "parentfield", "salary_component", "amount"], limit_page_length=0)
    for item in detail_rows:
        salary_component_map[(item.parent, item.parentfield, item.salary_component)] += flt(item.amount)

    output = []
    for slip in slips:
        selected_allocations = allocation_by_slip.get(slip.name) or []
        grouped = defaultdict(list)
        for item in selected_allocations:
            grouped[(item.project, item.funding_agreement, item.budget_line, item.donor, item.cost_center)].append(item)

        child_rows = []
        for key, items in grouped.items():
            project, agreement, budget_line, donor, cost_center = key
            row = base_row(slip)
            row.update(row_kind="Project Detail", indent=1, project=project,
                display_name=get_link_title("Project", project) or project or _("Unallocated"),
                funding_agreement=agreement,
                funding_agreement_title=get_link_title("Funding Agreement", agreement),
                donor=donor, budget_line=budget_line,
                budget_line_title=get_link_title("Budget Line", budget_line),
                cost_center=cost_center, allocation_run=items[0].allocation_run)
            apply_allocated_components(row, items)
            child_rows.append(row)

        # Preserve contractual/original work share and optionally normalize the visible scope to 100%.
        original_visible_total = sum(flt(row.allocation_percentage) for row in child_rows)
        for row in child_rows:
            row.original_allocation_percentage = flt(row.allocation_percentage)
        if allocation_scope and percentage_basis == "Selected Scope (100%)" and original_visible_total:
            assigned = 0
            for index, row in enumerate(child_rows):
                normalized = flt(row.original_allocation_percentage / original_visible_total * 100, 6)
                if index == len(child_rows) - 1:
                    normalized = flt(100 - assigned, 6)
                row.allocation_percentage = normalized
                assigned += normalized
        else:
            for row in child_rows:
                row.allocation_percentage = row.original_allocation_percentage

        if not child_rows and filters.get("show_unallocated") and not allocation_scope:
            row = base_row(slip)
            row.update(row_kind="Project Detail", indent=1, display_name=_("Unallocated"),
                project=None, allocation_percentage=0, allocated_amount=0,
                gross_pay=0, employer_contribution=0, employment_cost=0,
                total_deduction=0, net_pay=0, unallocated_amount=flt(slip.gross_pay))
            child_rows.append(row)

        if allocation_scope and not child_rows:
            continue

        total = base_row(slip)
        total.update(row_kind="Employee Total", indent=0,
            display_name=slip.employee_name or get_link_title("Employee", slip.employee) or slip.employee)
        if allocation_scope:
            total.gross_pay = sum(flt(x.gross_pay) for x in child_rows)
            total.employer_contribution = sum(flt(x.employer_contribution) for x in child_rows)
            total.employment_cost = sum(flt(x.employment_cost) for x in child_rows)
            total.total_deduction = sum(flt(x.total_deduction) for x in child_rows)
            total.net_pay = sum(flt(x.net_pay) for x in child_rows)
            total.allocated_amount = sum(flt(x.allocated_amount) for x in child_rows)
            total.original_allocation_percentage = sum(flt(x.original_allocation_percentage) for x in child_rows)
            total.allocation_percentage = 100 if percentage_basis == "Selected Scope (100%)" and child_rows else total.original_allocation_percentage
            total.outside_scope_amount = max(0, flt(slip.gross_pay) - total.gross_pay)
            total.unallocated_amount = 0
            for group, component in components:
                field = component_field(group, component)
                total[field] = sum(flt(x.get(field)) for x in child_rows)
        else:
            total.original_allocation_percentage = sum(flt(x.original_allocation_percentage) for x in child_rows)
            total.allocation_percentage = total.original_allocation_percentage
            total.allocated_amount = sum(flt(x.allocated_amount) for x in child_rows)
            total.outside_scope_amount = 0
            total.unallocated_amount = max(0, flt(slip.gross_pay) - sum(flt(x.gross_pay) for x in child_rows))
            total.employer_contribution = sum(flt(x.employer_contribution) for x in child_rows)
            total.employment_cost = flt(slip.gross_pay) + total.employer_contribution
            add_component_values(total, slip, components, salary_component_map, 100)
        output.append(total)
        output.extend(child_rows)
    return output


def apply_allocated_components(row, allocation_rows):
    gross = deduction = employer = allocated = 0
    work_shares = []
    for item in allocation_rows:
        amount = flt(item.company_currency_amount or item.allocated_amount)
        category = item.component_category or "Allocable Earning"
        group = "deductions" if category == "Employee Deduction" else "earnings"
        field = component_field(group, item.salary_component)
        row[field] = flt(row.get(field)) + amount
        if category == "Employee Deduction":
            deduction += amount
        elif category == "Employer Contribution":
            employer += amount
        elif category != "Informational":
            gross += amount
        if category not in ("Informational", "Employee Deduction"):
            allocated += amount
        if item.work_share is not None:
            work_shares.append(flt(item.work_share))
    row.gross_pay = gross
    row.total_deduction = deduction
    row.net_pay = gross - deduction
    row.employer_contribution = employer
    row.employment_cost = gross + employer
    row.allocated_amount = allocated
    row.allocation_percentage = max(work_shares) if work_shares else 0
    row.unallocated_amount = 0


def get_link_title(doctype, name):
    if not name:
        return None
    meta = frappe.get_meta(doctype)
    title_field = meta.get_title_field() if hasattr(meta, "get_title_field") else meta.title_field
    if title_field and meta.get("show_title_field_in_link"):
        return frappe.db.get_value(doctype, name, title_field) or name
    return name

def base_row(slip):
    return frappe._dict(employee=slip.employee, employee_name=slip.employee_name or get_link_title("Employee", slip.employee), salary_slip=slip.name, salary_slip_status={0: "Draft", 1: "Submitted", 2: "Cancelled"}.get(slip.docstatus), payroll_entry=slip.payroll_entry, department=slip.department, branch=slip.branch, designation=slip.designation, start_date=slip.start_date, end_date=slip.end_date, posting_date=slip.posting_date, gross_pay=flt(slip.gross_pay), employer_contribution=0, employment_cost=flt(slip.gross_pay), total_deduction=flt(slip.total_deduction), net_pay=flt(slip.net_pay), allocated_amount=0, unallocated_amount=0, outside_scope_amount=0, original_allocation_percentage=0, currency=slip.currency)


def component_field(group, component):
    return ("earning_" if group == "earnings" else "deduction_") + frappe.scrub(component)


def add_component_values(row, slip, components, component_map, percentage):
    for group, component in components:
        row[component_field(group, component)] = component_map[(slip.name, group, component)] * percentage / 100


def apply_view(rows, filters, access):
    mode = filters.get("view_mode") or "Employee with Project Details"
    if mode == "Employee with Project Details":
        return rows
    if mode in ("Employee Totals Only", "Government Payroll Register"):
        return [row for row in rows if row.row_kind == "Employee Total"]
    if mode == "Salary Component Analysis":
        return component_analysis(rows, filters)
    if mode in ("Project Summary", "Funding Agreement Summary", "Donor Summary", "Donor Statement"):
        field = {"Project Summary": "project", "Funding Agreement Summary": "funding_agreement", "Donor Summary": "donor", "Donor Statement": "donor"}[mode]
        return aggregate_rows([row for row in rows if row.row_kind == "Project Detail"], field)
    if mode == "Audit Review":
        return [row for row in rows if row.row_kind == "Project Detail"]
    return rows


def aggregate_rows(rows, field):
    grouped = {}
    for row in rows:
        key = row.get(field) or _("Unspecified")
        item = grouped.setdefault(key, frappe._dict(row_kind="Summary", display_name=get_link_title({"project":"Project","funding_agreement":"Funding Agreement","budget_line":"Budget Line"}.get(field, "Funding Agreement"), key) if field != "donor" else key, gross_pay=0, employer_contribution=0, employment_cost=0, total_deduction=0, net_pay=0, allocated_amount=0, unallocated_amount=0, outside_scope_amount=0, employees=set(), projects=set(), currency=row.currency))
        for metric in ("gross_pay", "employer_contribution", "employment_cost", "total_deduction", "net_pay"):
            item[metric] = flt(item.get(metric)) + flt(row.get(metric))
        item.allocated_amount += flt(row.allocated_amount)
        item.unallocated_amount += flt(row.unallocated_amount)
        item.outside_scope_amount += flt(row.get("outside_scope_amount"))
        for key, value in row.items():
            if key.startswith("earning_") or key.startswith("deduction_"):
                item[key] = flt(item.get(key)) + flt(value)
        item.employees.add(row.employee)
        if row.project:
            item.projects.add(row.project)
    out = []
    for item in grouped.values():
        item.employee_count = len(item.employees)
        item.project_count = len(item.projects)
        item.pop("employees")
        item.pop("projects")
        out.append(item)
    return sorted(out, key=lambda x: flt(x.allocated_amount), reverse=True)


def component_analysis(rows, filters):
    out = []
    show_zero = bool(filters.get("show_zero_components"))
    for row in rows:
        if row.row_kind != "Project Detail":
            continue
        for key, value in row.items():
            if not (key.startswith("earning_") or key.startswith("deduction_")):
                continue
            if not show_zero and not flt(value):
                continue
            item = frappe._dict(row)
            item.component_type = "Earning" if key.startswith("earning_") else "Deduction"
            item.salary_component = key.split("_", 1)[1].replace("_", " ").title()
            item.component_amount = flt(value)
            out.append(item)
    return out


def get_columns(filters, components, access):
    mode = filters.get("view_mode") or "Employee with Project Details"
    def col(field, label, fieldtype="Data", options=None, width=140, freeze=False):
        value = {"fieldname": field, "label": _(label), "fieldtype": fieldtype, "width": width}
        if options:
            value["options"] = options
        if freeze:
            value["freeze"] = 1
        return value
    if mode in ("Project Summary", "Funding Agreement Summary", "Donor Summary", "Donor Statement"):
        summary_columns = [col("display_name", "Group", width=220, freeze=True), col("employee_count", "Employees", "Int", width=95, freeze=True), col("project_count", "Projects", "Int", width=90)]
        for group, component in components:
            summary_columns.append(col(component_field(group, component), component, "Currency", "currency", 135))
        summary_columns.extend([col("gross_pay", "Gross Earnings", "Currency", "currency", 140), col("employer_contribution", "Employer Contributions", "Currency", "currency", 165), col("employment_cost", "Employment Cost", "Currency", "currency", 145), col("total_deduction", "Deductions", "Currency", "currency", 135), col("net_pay", "Net Pay", "Currency", "currency", 125), col("allocated_amount", "Allocated Payroll", "Currency", "currency", 150), col("unallocated_amount", "Unallocated Payroll", "Currency", "currency", 155), col("outside_scope_amount", "Outside Selected Scope", "Currency", "currency", 165), col("currency", "Currency", "Link", "Currency", 90)])
        return summary_columns
    if mode == "Salary Component Analysis":
        return [col("employee_name", "Employee Name", width=180, freeze=True), col("display_name", "Project", width=180, freeze=True), col("funding_agreement", "Funding Agreement", "Link", "Funding Agreement", 180), col("donor", "Donor", width=150), col("component_type", "Component Type", width=110), col("salary_component", "Salary Component", width=180), col("component_amount", "Allocated Component Amount", "Currency", "currency", 175), col("allocation_percentage", "Displayed Scope %", "Percent", width=115), col("original_allocation_percentage", "Original Payroll %", "Percent", width=120)]
    columns = [col("employee_name", "Employee Name", width=180, freeze=True), col("display_name", "Project / Total", width=190, freeze=True), col("employee", "Employee", "Link", "Employee", 125), col("salary_slip", "Salary Slip", "Link", "Salary Slip", 150), col("salary_slip_status", "Salary Slip Status", "Data", width=115), col("payroll_entry", "Payroll Entry", "Link", "Payroll Entry", 150), col("department", "Department", "Link", "Department", 140), col("branch", "Branch", "Link", "Branch", 125), col("designation", "Designation", "Link", "Designation", 135), col("funding_agreement", "Funding Agreement", "Link", "Funding Agreement", 175), col("funding_agreement_title", "Funding Agreement Title", "Data", width=190), col("donor", "Donor", width=140), col("budget_line", "Budget Line", "Link", "Budget Line", 155), col("allocation_percentage", "Displayed Scope %", "Percent", width=115), col("original_allocation_percentage", "Original Payroll %", "Percent", width=120)]
    for group, component in components:
        columns.append(col(component_field(group, component), component, "Currency", "currency", 135))
    columns.extend([col("gross_pay", "Gross Earnings", "Currency", "currency", 135), col("employer_contribution", "Employer Contributions", "Currency", "currency", 165), col("employment_cost", "Employment Cost", "Currency", "currency", 145), col("total_deduction", "Total Deductions", "Currency", "currency", 135), col("net_pay", "Net Pay", "Currency", "currency", 125), col("allocated_amount", "Allocated Payroll", "Currency", "currency", 145), col("unallocated_amount", "Unallocated Payroll", "Currency", "currency", 155), col("outside_scope_amount", "Outside Selected Scope", "Currency", "currency", 165), col("currency", "Currency", "Link", "Currency", 90)])
    if mode == "Audit Review":
        columns.extend([col("allocation_run", "Allocation Run", "Link", "Payroll Allocation Run", 165), col("posting_date", "Posting Date", "Date", width=105)])
    return columns


def get_summary(rows, filters):
    employee_rows = [row for row in rows if row.get("row_kind") == "Employee Total"]
    source = employee_rows or rows
    currency = next((row.get("currency") for row in source if row.get("currency")), None)
    employees = {row.get("employee") for row in source if row.get("employee")}
    projects = {row.get("project") for row in rows if row.get("project")}
    return [
        {"value": len(employees), "label": _("Employees"), "datatype": "Int", "indicator": "Blue"},
        {"value": len(projects), "label": _("Projects"), "datatype": "Int", "indicator": "Blue"},
        {"value": sum(flt(row.get("gross_pay")) for row in source), "label": _("Gross Payroll"), "datatype": "Currency", "currency": currency, "indicator": "Blue"},
        {"value": sum(flt(row.get("employer_contribution")) for row in source), "label": _("Employer Contributions"), "datatype": "Currency", "currency": currency, "indicator": "Purple"},
        {"value": sum(flt(row.get("employment_cost")) for row in source), "label": _("Employment Cost"), "datatype": "Currency", "currency": currency, "indicator": "Blue"},
        {"value": sum(flt(row.get("total_deduction")) for row in source), "label": _("Deductions"), "datatype": "Currency", "currency": currency, "indicator": "Orange"},
        {"value": sum(flt(row.get("net_pay")) for row in source), "label": _("Net Payroll"), "datatype": "Currency", "currency": currency, "indicator": "Green"},
        {"value": sum(flt(row.get("allocated_amount")) for row in rows if row.get("row_kind") != "Employee Total"), "label": _("Allocated Payroll"), "datatype": "Currency", "currency": currency, "indicator": "Purple"},
    ]


def get_chart(rows, filters):
    mode = filters.get("view_mode") or "Employee with Project Details"
    if mode in ("Employee Totals Only", "Government Payroll Register"):
        items = rows[:15]
        return {"data": {"labels": [row.employee_name or row.employee for row in items], "datasets": [{"name": _("Gross Pay"), "values": [flt(row.gross_pay) for row in items]}, {"name": _("Net Pay"), "values": [flt(row.net_pay) for row in items]}]}, "type": "bar"}
    groups = defaultdict(float)
    for row in rows:
        if row.get("row_kind") == "Employee Total":
            continue
        label = row.get("display_name") or row.get("project") or _("Unallocated")
        groups[label] += flt(row.get("allocated_amount"))
    items = sorted(groups.items(), key=lambda x: x[1], reverse=True)[:15]
    return {"data": {"labels": [x[0] for x in items], "datasets": [{"name": _("Allocated Payroll"), "values": [x[1] for x in items]}]}, "type": "bar"} if items else None


def get_message(filters, access):
    mode = filters.get("view_mode") or "Employee with Project Details"
    message = _("This report combines Salary Slips with Payroll Allocation Results. When allocation filters are active and Percentage Basis is Selected Scope (100%), displayed project percentages are normalized within the selected scope; amounts remain the actual allocated amounts, and Original Payroll % preserves the contractual payroll distribution.")
    message += " " + _("Percentage Basis: {0}.").format(filters.get("percentage_basis") or "Selected Scope (100%)")
    if access.get("aggregate_only"):
        message += " " + _("Your role is restricted to aggregated payroll information.")
    return f'<div class="alert alert-info"><strong>{_(mode)}</strong><br>{message}</div>'
