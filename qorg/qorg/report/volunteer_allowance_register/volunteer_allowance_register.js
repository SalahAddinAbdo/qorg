frappe.query_reports["Volunteer Allowance Register"]={filters:[
 {fieldname:"company",label:__("Company"),fieldtype:"Link",options:"Company",reqd:1,default:frappe.defaults.get_user_default("Company")},
 {fieldname:"from_date",label:__("From Date"),fieldtype:"Date",default:frappe.datetime.add_months(frappe.datetime.get_today(),-1)},
 {fieldname:"to_date",label:__("To Date"),fieldtype:"Date",default:frappe.datetime.get_today()},
 {fieldname:"accrual_type",label:__("Accrual Type"),fieldtype:"Link",options:"Service and Allowance Type",default:"Volunteer Allowance"},
 {fieldname:"project",label:__("Project"),fieldtype:"Link",options:"Project",get_query:()=>({filters:{company:frappe.query_report.get_filter_value("company")||""}})},
 {fieldname:"funding_agreement",label:__("Funding Agreement"),fieldtype:"Link",options:"Funding Agreement"},
 {fieldname:"operational_status",label:__("Status"),fieldtype:"Select",options:["","Draft","Under Review","Approved","Journal Draft Created","Posted","Partially Paid","Paid","Reversed"].join("\n")}
],onload(report){report.qorg_sticky_fieldnames=["accrual","payee_name"];setTimeout(()=>qorg.procurement_reports.configure_sticky_columns(report,report.qorg_sticky_fieldnames),250);},formatter(value,row,column,data,default_formatter){value=default_formatter(value,row,column,data);if(data&&data.eligibility_status==="Ineligible")value=`<span class="text-danger">${value}</span>`;return value;}};