frappe.provide('qorg.procurement_reports');
qorg.procurement_reports.after_datatable_render = function(report) {
  const wrapper = report.page && report.page.wrapper;
  if (!wrapper) return;
  const table = wrapper.querySelector('.dt-scrollable');
  if (table) table.classList.add('qorg-procurement-sticky');
};
