frappe.query_reports["Applicant Screening and Aging"]={filters:[]};
(function(){
  const report=frappe.query_reports["Applicant Screening and Aging"] || {};
  const original_formatter=report.formatter;
  report.formatter=function(value,row,column,data,default_formatter){
    let output=original_formatter?original_formatter(value,row,column,data,default_formatter):default_formatter(value,row,column,data);
    const raw=data && data[column.fieldname];
    if(column.fieldtype==="Percent" && raw!==null && raw!==undefined) output=`<span class="indicator-pill blue">${output}</span>`;
    if(["status","qorg_selection_status","qorg_screening_status","result"].includes(column.fieldname) && raw){
      const positive=["Active","Approved","Selected","Completed","Passed","Accepted","Issued","Cleared","Converted"].includes(raw);
      const negative=["Rejected","Failed","Cancelled","Terminated","Not Cleared","Screened Out"].includes(raw);
      output=`<span class="indicator-pill ${positive?"green":negative?"red":"orange"}">${frappe.utils.escape_html(String(raw))}</span>`;
    }
    return output;
  };
  const original_onload=report.onload;
  report.onload=function(query_report){
    if(original_onload) original_onload(query_report);
    query_report.page.add_inner_button(__("Reset Filters"),()=>{query_report.filters.forEach(filter=>filter.set_value(null));query_report.refresh();});
    if(!document.getElementById("qorg-report-summary-style")){const style=document.createElement("style");style.id="qorg-report-summary-style";style.textContent=".report-summary{display:flex;flex-wrap:wrap;gap:8px}.report-summary .summary-item{min-width:150px;flex:1 1 150px}";document.head.appendChild(style);}
  };
  frappe.query_reports["Applicant Screening and Aging"]=report;
})();
