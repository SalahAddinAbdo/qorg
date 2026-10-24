frappe.query_reports["Application Screening and Aging"] = {
  filters: [{"fieldname": "company", "label": "Company", "fieldtype": "Link", "options": "Company"}, {"fieldname": "project", "label": "Project", "fieldtype": "Link", "options": "Project"}, {"fieldname": "branch", "label": "Branch", "fieldtype": "Link", "options": "Branch"}, {"fieldname": "opportunity", "label": "Opportunity", "fieldtype": "Link", "options": "External Opportunity"}, {"fieldname": "status", "label": "Status", "fieldtype": "Data"}, {"fieldname": "external_person", "label": "External Person", "fieldtype": "Link", "options": "External Person"}],
  formatter(value,row,column,data,default_formatter) {
    value=default_formatter(value,row,column,data);
    if(column.fieldtype === "Percent" && value !== null && value !== undefined) value = `<span class="indicator-pill blue">${value}</span>`;
    if(column.fieldname === "status" && data && data.status) value = `<span class="indicator-pill ${["Active","Selected","Completed","Verified","Issued","Cleared"].includes(data.status)?"green":["Rejected","Terminated","Not Cleared"].includes(data.status)?"red":"orange"}">${frappe.utils.escape_html(data.status)}</span>`;
    return value;
  },
  onload(report) {
    report.page.add_inner_button(__("Reset Filters"),()=>{ report.filters.forEach(f=>f.set_value(null)); report.refresh(); });
    const style=document.createElement("style"); style.textContent=".report-summary .summary-item{min-width:150px;flex:1 1 150px}.report-summary{display:flex;flex-wrap:wrap;gap:8px}"; document.head.appendChild(style);
  }
};
