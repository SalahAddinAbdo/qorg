frappe.provide("qorg.procurement_reports");
qorg.procurement_reports.configure_sticky_columns=function(report,fieldnames=[]){
 const wrapper=report&&report.page&&report.page.wrapper;if(!wrapper)return;
 wrapper.classList.remove("qorg-report-sticky-enabled");wrapper.querySelectorAll(".qorg-sticky-column").forEach(c=>{c.classList.remove("qorg-sticky-column");c.style.insetInlineStart=""});
 if(!fieldnames.length)return;
 const columns=(report.datatable&&report.datatable.datamanager&&report.datatable.datamanager.columns)||[];let offset=0,applied=0;
 fieldnames.forEach(name=>{const index=columns.findIndex(c=>(c.id||c.fieldname||c.name)===name);if(index<0)return;const width=columns[index].width||120;wrapper.querySelectorAll(`.dt-cell--col-${index}`).forEach(c=>{c.classList.add("qorg-sticky-column");c.style.insetInlineStart=`${offset}px`;});offset+=width;applied++;});
 if(applied)wrapper.classList.add("qorg-report-sticky-enabled");
};
qorg.procurement_reports.after_datatable_render=function(report){
 const configured=(report&&report.qorg_sticky_fieldnames)||[];qorg.procurement_reports.configure_sticky_columns(report,configured);
};
