window.qorg_shared_cost_reports={
 options(values,txt){const q=(txt||"").toLowerCase();return values.filter(v=>v.toLowerCase().includes(q)).map(value=>({value,description:""}));},
 selected(name){const f=frappe.query_report?.get_filter(name);const v=f?.get_value()||[];return Array.isArray(v)?v:(v?[v]:[]);},
 filters(extra=[]){return [
  {fieldname:"view_mode",label:__("View"),fieldtype:"Select",options:["Executive","Donor","Operations","Audit"].join("\n"),default:"Executive"},
  {fieldname:"company",label:__("Company"),fieldtype:"Link",options:"Company",reqd:1,default:frappe.defaults.get_user_default("Company"),on_change(){["project","donor","funding_agreement"].forEach(x=>frappe.query_report.set_filter_value(x,[]));}},
  {fieldname:"from_date",label:__("From Date"),fieldtype:"Date",reqd:1,default:frappe.datetime.year_start()},
  {fieldname:"to_date",label:__("To Date"),fieldtype:"Date",reqd:1,default:frappe.datetime.get_today()},
  {fieldname:"project",label:__("Projects"),fieldtype:"MultiSelectList",get_data:txt=>frappe.db.get_link_options("Project",txt,{company:frappe.query_report.get_filter_value("company")}),on_change(){frappe.query_report.set_filter_value("funding_agreement",[]);}},
  {fieldname:"donor",label:__("Donors"),fieldtype:"MultiSelectList",get_data:txt=>frappe.db.get_link_options("Donor",txt)},
  {fieldname:"funding_agreement",label:__("Funding Agreements"),fieldtype:"MultiSelectList",get_data(txt){const projects=qorg_shared_cost_reports.selected("project"),donors=qorg_shared_cost_reports.selected("donor"),filters={company:frappe.query_report.get_filter_value("company")};if(projects.length)filters.project=["in",projects];if(donors.length)filters.donor=["in",donors];return frappe.db.get_link_options("Funding Agreement",txt,filters);}},
  ...extra
 ];},
 onload(report){report.page.add_inner_button(__("Reset Filters"),()=>{report.filters.forEach(f=>{if(!["company","from_date","to_date","view_mode"].includes(f.df.fieldname))f.set_value("");});report.set_filter_value("view_mode","Executive");report.refresh();});},
 after_refresh(report){setTimeout(()=>this.sticky(report),80);},
 sticky(report){const root=report.page?.wrapper?.[0];if(!root)return;root.classList.add("qorg-shared-cost-report");if(document.getElementById("qorg-shared-cost-sticky"))return;const style=document.createElement("style");style.id="qorg-shared-cost-sticky";style.textContent=`.qorg-shared-cost-report .dt-scrollable{overflow:auto}.qorg-shared-cost-report .dt-cell--col-0{position:sticky!important;inset-inline-start:0;z-index:4;background:var(--card-bg,#fff)}.qorg-shared-cost-report .dt-cell--col-1{position:sticky!important;inset-inline-start:160px;z-index:3;background:var(--card-bg,#fff)}`;document.head.appendChild(style);},
 formatter(value,row,column,data,default_formatter){value=default_formatter(value,row,column,data);if(["difference","unallocated_amount","variance"].includes(column.fieldname)&&Number(data?.[column.fieldname]))return `<span class="indicator-pill red">${value}</span>`;if(column.fieldname==="eligibility_status")return `<span class="indicator-pill ${data?.eligibility_status==="Eligible"?"green":"red"}">${value}</span>`;if(column.fieldname==="budget_status")return `<span class="indicator-pill ${data?.budget_status==="Within Budget"?"green":"red"}">${value}</span>`;return value;}
};
