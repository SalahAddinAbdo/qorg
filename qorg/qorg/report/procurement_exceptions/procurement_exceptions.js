frappe.query_reports["Procurement Exceptions"] = {
  filters: [
  {
    "fieldname": "company",
    "label": "Company",
    "fieldtype": "Link",
    "options": "Company"
  },
  {
    "fieldname": "project",
    "label": "Project",
    "fieldtype": "Link",
    "options": "Project"
  },
  {
    "fieldname": "status",
    "label": "Status",
    "fieldtype": "Select",
    "options": "Draft Setup\nSetup Approved\nPublished or Invited\nSubmission Closed\nOpening Completed\nTechnical Evaluation Approved\nFinancial Evaluation Approved\nCombined Evaluation Completed\nAward Approved\nClosed"
  },
  {
    "fieldname": "currency",
    "label": "Currency",
    "fieldtype": "Link",
    "options": "Currency"
  }
],
  formatter(value, row, column, data, default_formatter) {
    value = default_formatter(value, row, column, data);
    if (["status","submission_status","registration_status","risk_rating"].includes(column.fieldname)) {
      const v = (data && data[column.fieldname]) || "";
      const color = /approved|active|completed|closed|low/i.test(v) ? "green" : /rejected|terminated|critical|high|expired|overdue/i.test(v) ? "red" : /pending|review|progress|medium|submitted/i.test(v) ? "orange" : "blue";
      return `<span class="indicator-pill ${color}">${value}</span>`;
    }
    return value;
  }
};
