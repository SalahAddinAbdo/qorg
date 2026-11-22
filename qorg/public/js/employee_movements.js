frappe.ui.form.on('Employee', {
  refresh(frm) {
    if (frm.is_new()) return;
    frm.add_custom_button(__('Movement Timeline'), () => {
      frappe.call({ method:'qorg.qorg.employee_lifecycle.api.movement_timeline', args:{employee:frm.doc.name} }).then(r => {
        const rows=(r.message||[]).map(x=>`<tr><td>${frappe.utils.escape_html(x.effective_date||'')}</td><td>${frappe.utils.escape_html(x.doctype)}</td><td><a href="/app/${frappe.router.slug(x.doctype)}/${encodeURIComponent(x.name)}">${frappe.utils.escape_html(x.name)}</a></td><td>${frappe.utils.escape_html(x.reason||'')}</td></tr>`).join('');
        frappe.msgprint({title:__('Employment Movement Timeline'),message:`<table class="table table-bordered"><thead><tr><th>${__('Effective Date')}</th><th>${__('Type')}</th><th>${__('Document')}</th><th>${__('Reason')}</th></tr></thead><tbody>${rows}</tbody></table>`,wide:true});
      });
    }, __('Employee Lifecycle'));
  }
});
