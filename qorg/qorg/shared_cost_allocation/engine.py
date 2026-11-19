import json
import frappe
from frappe import _
from frappe.utils import flt, getdate, now_datetime
from qorg.qorg.shared_cost_allocation.validation import validate_rule

PAYROLL_VOUCHERS={"Payroll Entry","Salary Slip"}

def preview_run(doc):
    if not doc.allocation_rule:return
    rule=frappe.get_doc("Shared Cost Allocation Rule",doc.allocation_rule)
    company_settings=frappe.get_cached_doc("Company",rule.company)
    if not company_settings.get("custom_enable_shared_cost_allocation"):frappe.throw(_("Shared Cost Allocation is not enabled for Company {0}.").format(rule.company))
    if rule.docstatus!=1 or rule.status!="Active":frappe.throw(_("A submitted active allocation rule is required."))
    validate_rule(rule);rule._allocation_date=doc.posting_date;_apply_header(doc,rule);_validate_period(doc,rule);_validate_project_statuses(doc,rule)
    sources=_source_rows(doc,rule);doc.set("entries",[]);doc.source_entry_count=len(sources)
    total=_round(sum(flt(x.available_amount) for x in sources));doc.source_amount=total;doc.eligible_amount=total;doc.excluded_amount=0
    if rule.minimum_source_amount and total<flt(rule.minimum_source_amount):frappe.throw(_("Source amount is below the rule minimum source amount."))
    if rule.maximum_run_amount and total>flt(rule.maximum_run_amount):frappe.throw(_("Source amount exceeds the rule maximum run amount."))
    if rule.allocation_category=="Indirect Cost Recovery":_preview_indirect(doc,rule,sources,total)
    else:_preview_shared(doc,rule,sources,total)
    _enrich_currency_and_budget(doc,rule);doc.rule_snapshot=json.dumps(_snapshot(rule),default=str,sort_keys=True);doc.run_status="Previewed"

def _active_targets(rule):
    date=getdate(getattr(rule,"_allocation_date",rule.effective_from))
    return [r for r in rule.targets if r.allow_allocation and (not r.target_effective_from or getdate(r.target_effective_from)<=date) and (not r.target_effective_to or getdate(r.target_effective_to)>=date)]

def _preview_shared(doc,rule,sources,total):
    targets=_target_amounts(rule,doc,total);allocated=0
    for source in sources:
        source_amount=_round(source.available_amount)
        for target,target_total,basis,value in targets:
            amount=_round(source_amount*target_total/total) if total else 0;status,message=_eligibility(target,doc.posting_date)
            if status!="Eligible" and not rule.allow_budget_override:amount=0
            _append(doc,source,target,amount,target_total/total*100 if total else 0,status,message,basis,value);allocated+=amount
    _finish(doc,rule,total,allocated)

def _preview_indirect(doc,rule,sources,total):
    rate_row=_rate_for(rule,doc.posting_date);rate=flt(rate_row.indirect_cost_rate);base=_indirect_base(rule,doc,sources,total);gross=_round(base*rate/100);cap=flt(rate_row.period_cap) or flt(rule.total_recovery_cap)
    if cap:gross=min(gross,cap)
    prior=_prior_recovery(rule,doc,rate_row);desired=_round(gross-prior) if doc.run_type=="Adjustment" else gross
    if doc.run_type=="Adjustment" and not doc.adjustment_of:frappe.throw(_("Adjustment Of is required for an adjustment run."))
    doc.eligible_base_amount=base;doc.indirect_rate_applied=rate;doc.recovery_cap_applied=cap;doc.prior_recovery_amount=prior;doc.adjustment_amount=desired if doc.run_type=="Adjustment" else 0
    targets=_target_amounts(rule,doc,abs(desired));allocated=0;synthetic=frappe._dict(name="",voucher_type="Shared Cost Allocation Run",voucher_no=doc.name or "New Run",account=rule.indirect_cost_expense_account,cost_center=rule.source_cost_center,debit=desired,credit=0,available_amount=desired)
    sign=1 if desired>=0 else -1
    for target,amount,basis,value in targets:
        amount=_round(amount*sign);effective_rate=flt(target.indirect_rate_override) or rate
        if target.indirect_rate_override:amount=_round(base*effective_rate/100*(abs(amount)/abs(desired) if desired else 0))*sign
        target_cap=flt(target.target_cap) or flt(target.maximum_amount)
        if target_cap:amount=min(abs(amount),target_cap)*sign
        status,message=_eligibility(target,doc.posting_date)
        if target.donor_approval_required and not (target.donor_approval_reference or doc.donor_approval_reference):status,message="Ineligible",_("Donor approval reference is required.")
        if status!="Eligible" and not rule.allow_budget_override:amount=0
        _append(doc,synthetic,target,amount,abs(amount)/abs(desired)*100 if desired else 0,status,message,basis,value);allocated+=amount
    doc.eligible_amount=desired;_finish(doc,rule,desired,allocated)

def _indirect_base(rule,doc,sources,total):
    if rule.indirect_base_method=="Selected Accounts and Budget Lines":return total
    base=0
    for target in _active_targets(rule):
        filters={"company":rule.company,"project":target.project,"posting_date":["between",[doc.period_start,doc.period_end]],"is_cancelled":0}
        if frappe.get_meta("GL Entry").has_field("budget_line"):filters["budget_line"]=target.budget_line
        rows=frappe.get_all("GL Entry",filters=filters,fields=["debit","credit","account"])
        for row in rows:
            if rule.indirect_base_method=="Modified Total Direct Cost" and _is_excluded_mtdc_account(row.account):continue
            base+=flt(row.debit)-flt(row.credit)
    return _round(base or total)

def _is_excluded_mtdc_account(account):
    account_type=frappe.db.get_value("Account",account,"account_type")
    return account_type in ("Fixed Asset","Tax","Payable","Receivable")

def _driver_values(rule,doc,targets):
    method=rule.allocation_method
    values={r.name or str(r.idx):0 for r in targets}
    if method in ("Fixed Percentage","Fixed Amount","Equal Distribution","Manual Driver"):
        for r in targets:values[r.name or str(r.idx)]={"Fixed Percentage":flt(r.allocation_percentage),"Fixed Amount":flt(r.fixed_amount),"Equal Distribution":1,"Manual Driver":flt(r.driver_quantity)}[method]
        return values,method
    if method=="Direct Expenditure Ratio":
        for r in targets:values[r.name or str(r.idx)]=_project_expense(r.project,doc.period_start,doc.period_end,r.budget_line)
    elif method=="Funding or Budget Ratio":
        for r in targets:values[r.name or str(r.idx)]=flt(frappe.db.get_value("Budget Line",r.budget_line,"line_cost"))
    elif method=="Headcount":
        for r in targets:values[r.name or str(r.idx)]=frappe.db.count("Project Core Team Assignment",{"parent":r.project,"parenttype":"Project","parentfield":"custom_project_core_team","active":1})
    elif method=="Beneficiary Count":
        for r in targets:
            plan=frappe.db.get_value("Project Beneficiary Plan",{"project":r.project,"docstatus":["<",2]},["actual_individuals_total","planned_individuals_total"],as_dict=True) or {}
            values[r.name or str(r.idx)]=flt(plan.get("actual_individuals_total")) or flt(plan.get("planned_individuals_total"))
    elif method=="Composite Driver":
        components=[("direct",flt(rule.direct_expenditure_weight)),("budget",flt(rule.budget_weight)),("headcount",flt(rule.headcount_weight)),("beneficiary",flt(rule.beneficiary_weight)),("manual",flt(rule.manual_weight))]
        raw={}
        for r in targets:
            key=r.name or str(r.idx);raw[key]={"direct":_project_expense(r.project,doc.period_start,doc.period_end,r.budget_line),"budget":flt(frappe.db.get_value("Budget Line",r.budget_line,"line_cost")),"headcount":frappe.db.count("Project Core Team Assignment",{"parent":r.project,"parenttype":"Project","parentfield":"custom_project_core_team","active":1}),"manual":flt(r.driver_quantity)}
            plan=frappe.db.get_value("Project Beneficiary Plan",{"project":r.project,"docstatus":["<",2]},["actual_individuals_total","planned_individuals_total"],as_dict=True) or {};raw[key]["beneficiary"]=flt(plan.get("actual_individuals_total")) or flt(plan.get("planned_individuals_total"))
        totals={c:sum(raw[k][c] for k in raw) for c,_ in components}
        for key in raw:values[key]=sum((raw[key][c]/totals[c] if totals[c] else 0)*w for c,w in components)
    return values,method

def _project_expense(project,start,end,budget_line=None):
    filters={"project":project,"posting_date":["between",[start,end]],"is_cancelled":0};meta=frappe.get_meta("GL Entry")
    if budget_line and meta.has_field("budget_line"):filters["budget_line"]=budget_line
    return _round(sum(flt(r.debit)-flt(r.credit) for r in frappe.get_all("GL Entry",filters=filters,fields=["debit","credit"])))

def _target_amounts(rule,doc,total):
    active=_active_targets(rule);values,basis=_driver_values(rule,doc,active);den=sum(abs(flt(v)) for v in values.values())
    if not den:frappe.throw(_("The selected allocation driver produced a zero total. Enter or generate valid driver values."))
    result=[]
    for r in active:
        value=flt(values[r.name or str(r.idx)])
        amount=flt(r.fixed_amount) if rule.allocation_method=="Fixed Amount" else total*abs(value)/den
        if r.maximum_amount:amount=min(amount,flt(r.maximum_amount))
        result.append((r,amount,basis,value))
    return result

def _finish(doc,rule,total,allocated):
    difference=_round(total-allocated)
    if difference and rule.difference_handling=="Allocate Rounding Difference":
        eligible=[r for r in doc.entries if r.eligibility_status=="Eligible"]
        if eligible:
            chosen=max(eligible,key=lambda x:abs(flt(x.allocated_amount))) if rule.rounding_method=="Largest Share" else eligible[-1];chosen.allocated_amount=_round(flt(chosen.allocated_amount)+difference);allocated+=difference;difference=0
    doc.allocated_amount=_round(allocated);doc.unallocated_amount=_round(total-allocated);doc.rounding_difference=difference
    if abs(flt(doc.unallocated_amount))>0.005 and not rule.allow_partial_allocation:frappe.throw(_("The run has an unallocated amount of {0}. Resolve exceptions or allow partial allocation.").format(doc.unallocated_amount))

def _apply_header(doc,rule):
    doc.company=rule.company;doc.allocation_category=rule.allocation_category;doc.allocation_method=rule.allocation_method;doc.source_cost_center=rule.source_cost_center or frappe.get_cached_value("Company",rule.company,"custom_shared_cost_default_cost_center");doc.company_currency=frappe.get_cached_value("Company",rule.company,"default_currency")

def _validate_period(doc,rule):
    if getdate(doc.period_end)<getdate(doc.period_start):frappe.throw(_("Period End cannot be before Period Start."))
    if getdate(doc.period_start)<getdate(rule.effective_from) or (rule.effective_to and getdate(doc.period_end)>getdate(rule.effective_to)):frappe.throw(_("The allocation period is outside the rule validity period."))

def _validate_project_statuses(doc,rule):
    company=frappe.get_cached_doc("Company",rule.company)
    for target in _active_targets(rule):
        closed=frappe.db.exists("Project Closure",{"project":target.project,"status":"Approved"}) or frappe.db.get_value("Project",target.project,"status") in ("Completed","Cancelled")
        if closed and not (doc.run_type=="Adjustment" and company.get("custom_allow_post_closeout_adjustment") and doc.donor_approval_reference):frappe.throw(_("Project {0} is closed. Only a donor-approved post-closeout adjustment is permitted by Company settings.").format(target.project))

def _accounts(rule):
    include=[];exclude=[]
    for row in rule.source_filters:
        target=include if row.filter_type=="Include" else exclude;target.append(row.account)
        if row.include_children:
            bounds=frappe.db.get_value("Account",row.account,["lft","rgt"],as_dict=True);target.extend(frappe.get_all("Account",filters={"lft":[">",bounds.lft],"rgt":["<",bounds.rgt],"company":rule.company},pluck="name"))
    return list(set(include)),list(set(exclude))

def _source_rows(doc,rule):
    include,exclude=_accounts(rule);source_cost_center=rule.source_cost_center or frappe.get_cached_value("Company",rule.company,"custom_shared_cost_default_cost_center")
    if not source_cost_center:frappe.throw(_("Set a Source Cost Center on the rule or a Default Shared Cost Center on Company."))
    filters={"company":doc.company,"posting_date":["between",[doc.period_start,doc.period_end]],"cost_center":source_cost_center,"is_cancelled":0}
    if rule.source_project:filters["project"]=rule.source_project
    elif rule.require_unassigned_project:filters["project"]=["in",["",None]]
    if rule.finance_book:filters["finance_book"]=rule.finance_book
    if include:filters["account"]=["in",include]
    if rule.voucher_types:filters["voucher_type"]=["in",[x.strip() for x in rule.voucher_types.split(",") if x.strip()]]
    rows=[] if rule.source_selection_mode=="Selected Vouchers Only" else frappe.get_all("GL Entry",filters=filters,fields=["name","account","cost_center","project","voucher_type","voucher_no","posting_date","debit","credit"],order_by="posting_date,name")
    selected={(r.voucher_type,r.voucher_no) for r in rule.selected_vouchers if r.include}
    excluded_selected={(r.voucher_type,r.voucher_no) for r in rule.selected_vouchers if not r.include}
    if rule.source_selection_mode in ("Selected Vouchers Only","Filtered GL Entries plus Selected Vouchers") and selected:
        rows.extend(frappe.get_all("GL Entry",filters={"company":doc.company,"is_cancelled":0,"voucher_no":["in",[x[1] for x in selected]]},fields=["name","account","cost_center","project","voucher_type","voucher_no","posting_date","debit","credit"]))
    submitted=frappe.get_all("Shared Cost Allocation Run",filters={"docstatus":1,"name":["!=",doc.name or ""]},pluck="name");payroll_group=frappe.get_cached_value("Company",rule.company,"custom_payroll_account_group") if rule.exclude_payroll_accounts else None;payroll_accounts=set()
    if payroll_group:
        b=frappe.db.get_value("Account",payroll_group,["lft","rgt"],as_dict=True);payroll_accounts=set(frappe.get_all("Account",filters={"lft":[">=",b.lft],"rgt":["<=",b.rgt],"company":rule.company},pluck="name"))
    unique={}
    for row in rows:
        if rule.source_selection_mode=="Selected Vouchers Only" and (row.voucher_type,row.voucher_no) not in selected:continue
        if (row.voucher_type,row.voucher_no) in excluded_selected or row.account in exclude or row.account in payroll_accounts or row.voucher_type in PAYROLL_VOUCHERS:continue
        original=flt(row.debit)-flt(row.credit)
        prior=_previously_allocated(row.name,submitted)
        available=_round(original-prior)
        if available>0.005:row.available_amount=available;unique[row.name]=row
    if not unique:frappe.throw(_("No eligible General Ledger entries or remaining unallocated balances were found."))
    return list(unique.values())

def _previously_allocated(gl_entry,submitted_runs):
    if not submitted_runs:return 0
    return _round(sum(flt(x.allocated_amount) for x in frappe.get_all("Shared Cost Allocation Entry",filters={"source_gl_entry":gl_entry,"parent":["in",submitted_runs]},fields=["allocated_amount"])))

def _rate_for(rule,date):
    rows=[r for r in rule.rate_periods if getdate(r.effective_from)<=getdate(date) and (not r.effective_to or getdate(r.effective_to)>=getdate(date))]
    if len(rows)!=1:frappe.throw(_("Exactly one indirect cost rate must apply on the posting date."))
    return rows[0]

def _prior_recovery(rule,doc,rate_row):
    if doc.run_type!="Adjustment":return 0
    rows=frappe.get_all("Shared Cost Allocation Run",filters={"allocation_rule":rule.name,"allocation_category":"Indirect Cost Recovery","docstatus":1,"posting_date":["between",[rate_row.effective_from,rate_row.effective_to or doc.posting_date]],"name":["!=",doc.name or ""]},fields=["allocated_amount"])
    return _round(sum(flt(x.allocated_amount) for x in rows))

def _eligibility(target,date):
    if target.eligibility_start_date and getdate(date)<getdate(target.eligibility_start_date):return "Ineligible",_("Posting date is before funding eligibility.")
    if target.eligibility_end_date and getdate(date)>getdate(target.eligibility_end_date):return "Ineligible",_("Posting date is after funding eligibility.")
    return "Eligible",""

def _append(doc,source,target,amount,percent,status,message,basis,value):
    doc.append("entries",{"source_reference":source.name or source.voucher_no,"entry_type":"Indirect Recovery" if doc.allocation_category=="Indirect Cost Recovery" and doc.run_type!="Adjustment" else ("Adjustment" if doc.run_type=="Adjustment" else "Source Allocation"),"source_gl_entry":source.name or None,"source_voucher_type":source.voucher_type,"source_voucher":source.voucher_no,"source_account":source.account,"source_cost_center":source.cost_center,"source_amount":flt(source.available_amount),"project":target.project,"cost_center":target.cost_center,"budget_line":target.budget_line,"funding_agreement":target.funding_agreement,"donor":target.donor,"allocation_percentage":percent,"allocated_amount":amount,"driver_basis":basis,"driver_value":value,"eligibility_status":status,"exception_message":message})

def _enrich_currency_and_budget(doc,rule):
    donor_total=0;over=0
    for row in doc.entries:
        row.company_currency=doc.company_currency;row.allocated_company_amount=row.allocated_amount
        fa=frappe.db.get_value("Funding Agreement",row.funding_agreement,["agreement_currency","exchange_rate","exchange_rate_type","manual_rate_approval_reference","exchange_rate_source"],as_dict=True) if row.funding_agreement else None
        row.donor_currency=fa.agreement_currency if fa else doc.company_currency
        if fa and row.donor_currency!=doc.company_currency:
            from qorg.qorg.finance_budget_grants.currency import exchange_rate
            row.donor_exchange_rate=exchange_rate(row.donor_currency,doc.company_currency,doc.posting_date,fa.exchange_rate_type,fa.exchange_rate,fa.manual_rate_approval_reference,fa.exchange_rate_source)
        else:row.donor_exchange_rate=1
        row.allocated_donor_amount=_round(flt(row.allocated_amount)/(row.donor_exchange_rate or 1));donor_total+=row.allocated_donor_amount
        approved=flt(frappe.db.get_value("Budget Line",row.budget_line,"line_cost"));used=_budget_used(row.budget_line,row.project);row.budget_available_before=_round(approved-used);row.budget_available_after=_round(row.budget_available_before-flt(row.allocated_amount));row.budget_status="Within Budget" if row.budget_available_after>=-0.005 else "Over Budget"
        if row.budget_status=="Over Budget":over+=1
        if row.budget_status=="Over Budget" and not rule.allow_budget_override:row.eligibility_status="Exception";row.exception_message=_("Allocation exceeds the available Budget Line amount.")
    doc.donor_currency_total=_round(donor_total);doc.over_budget_entries=over
    if over and not rule.allow_budget_override:frappe.throw(_("{0} allocation entries exceed their Budget Line availability.").format(over))

def _budget_used(budget_line,project):
    meta=frappe.get_meta("GL Entry")
    if not meta.has_field("budget_line"):return 0
    return _round(sum(flt(x.debit)-flt(x.credit) for x in frappe.get_all("GL Entry",filters={"budget_line":budget_line,"project":project,"is_cancelled":0},fields=["debit","credit"])))

def _round(value):return flt(value,2)
def _snapshot(rule):return {"rule":rule.name,"version":rule.rule_version,"category":rule.allocation_category,"method":rule.allocation_method,"source_mode":rule.source_selection_mode,"effective_from":rule.effective_from,"effective_to":rule.effective_to,"targets":[{"project":r.project,"budget_line":r.budget_line,"funding_agreement":r.funding_agreement,"percentage":r.allocation_percentage,"fixed_amount":r.fixed_amount,"driver":r.driver_quantity,"from":r.target_effective_from,"to":r.target_effective_to} for r in rule.targets if r.allow_allocation],"rates":[{"from":r.effective_from,"to":r.effective_to,"rate":r.indirect_cost_rate,"cap":r.period_cap,"approval":r.donor_approval_reference} for r in rule.rate_periods]}

def post_run(doc):
    preview_run(doc);rule=frappe.get_doc("Shared Cost Allocation Rule",doc.allocation_rule)
    if abs(flt(doc.unallocated_amount))>0.005 and not rule.allow_partial_allocation:frappe.throw(_("The allocation is not fully balanced."))
    je=frappe.new_doc("Journal Entry");je.company=doc.company;je.posting_date=doc.posting_date;je.voucher_type="Journal Entry";je.user_remark=_("{0} allocation {1}").format(doc.allocation_category,doc.name);meta=frappe.get_meta("Journal Entry Account");grouped={}
    if rule.allocation_category=="Indirect Cost Recovery":
        for row in doc.entries:
            if not flt(row.allocated_amount):continue
            value=abs(flt(row.allocated_amount));account={"account":rule.indirect_cost_expense_account,"cost_center":row.cost_center,"project":row.project};account["debit_in_account_currency" if flt(row.allocated_amount)>0 else "credit_in_account_currency"]=value
            if meta.has_field("budget_line"):account["budget_line"]=row.budget_line
            if meta.has_field("funding_agreement"):account["funding_agreement"]=row.funding_agreement
            je.append("accounts",account)
        recovery={"account":rule.indirect_cost_recovery_account,"cost_center":rule.source_cost_center};recovery["credit_in_account_currency" if flt(doc.allocated_amount)>0 else "debit_in_account_currency"]=abs(flt(doc.allocated_amount));je.append("accounts",recovery)
    else:
        for row in doc.entries:
            if flt(row.allocated_amount)<=0:continue
            grouped[(row.source_account,row.source_cost_center)]=grouped.get((row.source_account,row.source_cost_center),0)+flt(row.allocated_amount);account={"account":row.source_account,"debit_in_account_currency":row.allocated_amount,"cost_center":row.cost_center,"project":row.project}
            if meta.has_field("budget_line"):account["budget_line"]=row.budget_line
            if meta.has_field("funding_agreement"):account["funding_agreement"]=row.funding_agreement
            je.append("accounts",account)
        for (account,cost_center),amount in grouped.items():je.append("accounts",{"account":account,"credit_in_account_currency":amount,"cost_center":cost_center})
    je.insert();je.submit();doc.db_set("journal_entry",je.name,update_modified=False);doc.db_set("run_status","Posted",update_modified=False);doc.db_set("processed_on",now_datetime(),update_modified=False);doc.db_set("processed_by",frappe.session.user,update_modified=False);doc.db_set("reconciliation_status","Matched",update_modified=False)
    for row in doc.entries:row.db_set("journal_entry",je.name,update_modified=False)

def reverse_run(doc):
    if not doc.journal_entry:return
    je=frappe.get_doc("Journal Entry",doc.journal_entry)
    if je.docstatus==1:je.cancel()
    doc.db_set("run_status","Reversed",update_modified=False);doc.db_set("reconciliation_status","Reversed",update_modified=False)

@frappe.whitelist()
def create_changed_rule(source_rule,change_type="Prospective Change",change_effective_date=None):
    source=frappe.get_doc("Shared Cost Allocation Rule",source_rule);source.check_permission("read")
    if source.docstatus!=1:frappe.throw(_("Only a submitted rule can be superseded."))
    if not frappe.has_permission("Shared Cost Allocation Rule","create"):frappe.throw(_("Not permitted to create an allocation rule."),frappe.PermissionError)
    doc=frappe.copy_doc(source);doc.name=None;doc.docstatus=0;doc.status="Draft";doc.supersedes_rule=source.name;doc.change_type=change_type;doc.change_effective_date=change_effective_date;doc.effective_from=change_effective_date or source.effective_from;doc.effective_to=None;doc.rule_version=_next_version(source.rule_version);doc.amended_from=None;doc.insert();return doc.name

def _next_version(value):
    try:major,minor=(str(value or "1.0").split(".")+["0"])[:2];return f"{int(major)}.{int(minor)+1}"
    except Exception:return "2.0"
