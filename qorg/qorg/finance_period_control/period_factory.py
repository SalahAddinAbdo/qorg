import calendar
import frappe
from frappe.utils import getdate

def basis():return frappe.db.get_single_value("Accounts Settings","qorg_budget_period_basis") or "Fiscal Year"
def validate_period(period):
    mode=basis();start=getdate(period.from_date);end=getdate(period.to_date)
    if mode=="Fiscal Year" and not period.fiscal_year:frappe.throw("Fiscal Year is required by Budget Period Basis")
    if mode=="Calendar Month" and (start.day!=1 or start.year!=end.year or start.month!=end.month or end.day!=calendar.monthrange(end.year,end.month)[1]):frappe.throw("Calendar Month periods must cover one complete calendar month")

def ensure_periods(company,fiscal_year=None,year=None,dry_run=False):
    mode=basis();spec=[]
    if mode=="Fiscal Year":
        if not fiscal_year:frappe.throw("Fiscal Year is required")
        fy=frappe.get_doc("Fiscal Year",fiscal_year);spec=[(f"{company}-{fiscal_year}",f"{fiscal_year} - {company}",fy.year_start_date,fy.year_end_date,fiscal_year)]
    elif mode=="Calendar Month":
        if not year:frappe.throw("Year is required")
        for month in range(1,13):
            end=calendar.monthrange(int(year),month)[1];code=f"{company}-{int(year):04d}-{month:02d}";spec.append((code,calendar.month_name[month]+f" {year} - {company}",f"{year}-{month:02d}-01",f"{year}-{month:02d}-{end:02d}",None))
    else:frappe.throw("Custom Period basis requires manual Budget Period creation")
    created=[]
    for code,name,start,end,fy in spec:
        if frappe.db.exists("Budget Period",code):continue
        created.append(code)
        if not dry_run:frappe.get_doc({"doctype":"Budget Period","period_code":code,"period_name":name,"company":company,"from_date":start,"to_date":end,"fiscal_year":fy,"status":"Draft","allow_commitments":1,"allow_actuals":1}).insert(ignore_permissions=True)
    return {"basis":mode,"created":created,"dry_run":dry_run}
@frappe.whitelist()
def generate(company,fiscal_year=None,year=None,dry_run=0):return ensure_periods(company,fiscal_year,year,bool(int(dry_run)))
