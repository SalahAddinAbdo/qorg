frappe.query_reports["Supplier Due Diligence"] = {
  filters: [
  {
    "fieldname": "supplier",
    "label": "Supplier",
    "fieldtype": "Link",
    "options": "Supplier"
  },
  {
    "fieldname": "registration_status",
    "label": "Registration Status",
    "fieldtype": "Select",
    "options": "Draft\nSubmitted\nUnder Due Diligence\nApproved\nRejected"
  },
  {
    "fieldname": "risk_rating",
    "label": "Risk Rating",
    "fieldtype": "Select",
    "options": "Low\nMedium\nHigh\nCritical"
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
