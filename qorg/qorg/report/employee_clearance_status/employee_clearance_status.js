const ms=(fieldname,label,options,get_data)=>({fieldname,label:__(label),fieldtype:"MultiSelectList",options,get_data});
frappe.query_reports["Employee Clearance Status"]={filters:[
{fieldname:"view",label:__("View"),fieldtype:"Select",options:"Executive\nHR\nFinance and Payroll\nAssets and Stock\nIT and Access\nFull",default:"Executive",reqd:1},
ms("companies","Companies","Company",txt=>frappe.db.get_link_options("Company",txt)),
ms("branches","Branches","Branch",txt=>frappe.db.get_link_options("Branch",txt,{company:["in",frappe.query_report.get_filter_value("companies")||[]]})),
ms("departments","Departments","Department",txt=>frappe.db.get_link_options("Department",txt,{company:["in",frappe.query_report.get_filter_value("companies")||[]]})),
ms("designations","Designations","Designation",txt=>frappe.db.get_link_options("Designation",txt)),
ms("employees","Employees","Employee",txt=>frappe.db.get_link_options("Employee",txt,{company:["in",frappe.query_report.get_filter_value("companies")||[]],branch:["in",frappe.query_report.get_filter_value("branches")||[]],department:["in",frappe.query_report.get_filter_value("departments")||[]]})),
ms("clearance_statuses","Clearance Statuses",null,txt=>["Not Started","In Progress","Blocked","Ready for Approval","Completed","Reopened"].filter(x=>x.toLowerCase().includes((txt||"").toLowerCase())).map(x=>({value:x,description:""}))),
{fieldname:"last_working_date_from",label:__("Last Working Date From"),fieldtype:"Date"},{fieldname:"last_working_date_to",label:__("Last Working Date To"),fieldtype:"Date"},
{fieldname:"overdue_only",label:__("Overdue Only"),fieldtype:"Check"},{fieldname:"has_outstanding",label:__("Has Outstanding Amount"),fieldtype:"Check"},{fieldname:"reopened_only",label:__("Reopened Only"),fieldtype:"Check"},
{fieldname:"group_by",label:__("Group By"),fieldtype:"Select",options:"None\nCompany\nBranch\nDepartment\nDesignation\nOverall Status",default:"None"}],
formatter(value,row,column,data,default_formatter){value=default_formatter(value,row,column,data);if(column.fieldname==="overall_status"&&data){const c=data.overall_status==="Completed"?"green":data.overall_status==="Blocked"?"red":"orange";return `<span class="indicator-pill ${c}">${frappe.utils.escape_html(data.overall_status||"")}</span>`;}return value;}};
