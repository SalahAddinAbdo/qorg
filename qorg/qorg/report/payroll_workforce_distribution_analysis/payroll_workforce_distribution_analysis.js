function qorg_payroll_sticky(report) {
  report.page.wrapper.addClass("qorg-payroll-workforce-analysis");
  if (document.getElementById("qorg-payroll-workforce-analysis-css")) return;
  const style = document.createElement("style");
  style.id = "qorg-payroll-workforce-analysis-css";
  style.textContent = `
    .qorg-payroll-workforce-analysis .dt-row .dt-cell--col-0 {position:sticky;left:0;z-index:4;background:var(--fg-color)}
    .qorg-payroll-workforce-analysis .dt-row .dt-cell--col-1 {position:sticky;left:180px;z-index:4;background:var(--fg-color);box-shadow:3px 0 5px rgba(0,0,0,.08)}
    [dir=rtl] .qorg-payroll-workforce-analysis .dt-row .dt-cell--col-0 {left:auto;right:0}
    [dir=rtl] .qorg-payroll-workforce-analysis .dt-row .dt-cell--col-1 {left:auto;right:180px;box-shadow:-3px 0 5px rgba(0,0,0,.08)}
    .qorg-payroll-workforce-analysis .qorg-employee-total {font-weight:700;background:var(--control-bg)}
  `;
  document.head.appendChild(style);
}

const qorg_multi_link = (fieldname, label, options, get_filters) => ({
  fieldname, label: __(label), fieldtype: "MultiSelectList",
  get_data(txt) { return frappe.db.get_link_options(options, txt, get_filters ? get_filters() : {}); },
  on_change() { if (frappe.query_report) frappe.query_report.refresh(); }
});

frappe.query_reports["Payroll Workforce Distribution Analysis"] = {
  filters: [
    {fieldname:"company",label:__("Company"),fieldtype:"Link",options:"Company",reqd:1,default:frappe.defaults.get_user_default("Company")},
    {fieldname:"from_date",label:__("From Date"),fieldtype:"Date",reqd:1,default:frappe.datetime.year_start()},
    {fieldname:"to_date",label:__("To Date"),fieldtype:"Date",reqd:1,default:frappe.datetime.get_today()},
    {fieldname:"period_basis",label:__("Period Basis"),fieldtype:"Select",default:"Period Overlap",options:"Posting Date\nEnd Date\nPeriod Overlap\nFully Within Period"},
    {fieldname:"salary_slip_status",label:__("Salary Slip Status"),fieldtype:"Select",reqd:1,default:"Submitted",options:"Draft\nSubmitted\nDraft and Submitted\nAll"},
    {fieldname:"percentage_basis",label:__("Percentage Basis"),fieldtype:"Select",reqd:1,default:"Selected Scope (100%)",options:"Selected Scope (100%)\nOriginal Payroll Distribution"},
    {fieldname:"view_mode",label:__("View Mode"),fieldtype:"Select",reqd:1,default:"Employee with Project Details",options:"Employee with Project Details\nEmployee Totals Only\nProject Summary\nFunding Agreement Summary\nDonor Summary\nGovernment Payroll Register\nAudit Review\nDonor Statement\nSalary Component Analysis"},
    {fieldname:"allocation_status",label:__("Allocation Status"),fieldtype:"Select",default:"Posted and Reconciled",options:"All Active\nApproved\nPosted\nPosted and Reconciled\nReconciled\nClosed\nReversed"},
    qorg_multi_link("employee","Employee","Employee",()=>({company:frappe.query_report.get_filter_value("company")})),
    qorg_multi_link("project","Project","Project",()=>({company:frappe.query_report.get_filter_value("company")})),
    qorg_multi_link("funding_agreement","Funding Agreement","Funding Agreement",()=>({docstatus:1})),
    {fieldname:"donor",label:__("Donor"),fieldtype:"MultiSelectList",get_data(txt){return frappe.call({method:"qorg.qorg.report.payroll_workforce_distribution_analysis.payroll_workforce_distribution_analysis.get_donor_options",args:{txt}}).then(r=>r.message||[]);}},
    qorg_multi_link("budget_line","Budget Line","Budget Line",()=>({is_group:0})),
    qorg_multi_link("department","Department","Department"),
    qorg_multi_link("branch","Branch","Branch"),
    qorg_multi_link("designation","Designation","Designation"),
    qorg_multi_link("payroll_entry","Payroll Entry","Payroll Entry",()=>({company:frappe.query_report.get_filter_value("company")})),
    qorg_multi_link("salary_component","Salary Component","Salary Component"),
    {fieldname:"component_type",label:__("Component Type"),fieldtype:"Select",options:"\nEarning\nDeduction"},
    {fieldname:"minimum_amount",label:__("Minimum Amount"),fieldtype:"Currency",default:0},
    {fieldname:"show_unallocated",label:__("Show Unallocated Payroll"),fieldtype:"Check",default:1},
    {fieldname:"show_zero_components",label:__("Show Zero Components"),fieldtype:"Check",default:0,depends_on:"eval:doc.view_mode=='Salary Component Analysis'"}
  ],
  formatter(value,row,column,data,default_formatter) {
    value = default_formatter(value,row,column,data);
    if (!data) return value;
    if (data.row_kind === "Employee Total") return `<div class="qorg-employee-total">${value}</div>`;
    if (data.row_kind === "Project Detail" && column.fieldname === "display_name") return `<span style="padding-inline-start:18px;color:var(--primary)">↳ ${value}</span>`;
    if (["allocation_percentage","original_allocation_percentage","gross_pay","total_deduction","net_pay","allocated_amount","unallocated_amount"].includes(column.fieldname)) return `<span style="font-weight:600">${value}</span>`;
    return value;
  },
  onload(report) {
    qorg_payroll_sticky(report);
    ["company","from_date","to_date","salary_slip_status","period_basis","percentage_basis","view_mode","allocation_status","component_type","minimum_amount","show_unallocated","show_zero_components"].forEach(name => {
      const filter = report.get_filter(name); if (filter && filter.df) filter.df.on_change = () => report.refresh();
    });
    const set_view = view => { report.set_filter_value("view_mode",view); report.refresh(); };
    report.page.add_inner_button(__("Government Register"),()=>set_view("Government Payroll Register"),__("View"));
    report.page.add_inner_button(__("Audit Review"),()=>set_view("Audit Review"),__("View"));
    report.page.add_inner_button(__("Donor Statement"),()=>set_view("Donor Statement"),__("View"));
    report.page.add_inner_button(__("Employee Details"),()=>set_view("Employee with Project Details"),__("View"));
  }
};
