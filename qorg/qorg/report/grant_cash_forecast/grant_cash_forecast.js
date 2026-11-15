frappe.query_reports["Grant Cash Forecast"] = {
  filters: [
    {fieldname:"company", label:__("Company"), fieldtype:"Link", options:"Company"},
    {fieldname:"project", label:__("Project"), fieldtype:"Link", options:"Project"},
    {fieldname:"donor", label:__("Donor"), fieldtype:"Link", options:"Donor"},
    {fieldname:"funding_agreement", label:__("Funding Agreement"), fieldtype:"Link", options:"Funding Agreement"},
    {fieldname:"status", label:__("Status"), fieldtype:"Select", options:"\nDraft\nUnder Review\nActive\nSuspended\nClosing\nClosed\nCancelled"},
    {fieldname:"from_date", label:__("From Date"), fieldtype:"Date"},
    {fieldname:"to_date", label:__("To Date"), fieldtype:"Date"}
  ]
};
