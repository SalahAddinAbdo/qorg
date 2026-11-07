frappe.query_reports["Bid Version Register"] = {
  filters: [
  {
    "fieldname": "procurement_process",
    "label": "Procurement Process",
    "fieldtype": "Link",
    "options": "Procurement Process"
  },
  {
    "fieldname": "supplier",
    "label": "Supplier",
    "fieldtype": "Link",
    "options": "Supplier"
  },
  {
    "fieldname": "supplier_registration",
    "label": "Supplier Profile",
    "fieldtype": "Link",
    "options": "Supplier Registration"
  },
  {
    "fieldname": "submission_status",
    "label": "Submission Status",
    "fieldtype": "Select",
    "options": "Draft\nSubmitted\nWithdrawn\nLate\nOpened\nUnder Evaluation\nDisqualified\nAccepted"
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
