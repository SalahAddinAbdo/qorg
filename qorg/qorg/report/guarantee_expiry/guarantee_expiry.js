frappe.query_reports["Guarantee Expiry"] = {
  filters: [
  {
    "fieldname": "status",
    "label": "Status",
    "fieldtype": "Select",
    "options": "Draft\nActive\nExpired\nReleased\nCalled"
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
