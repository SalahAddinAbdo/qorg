frappe.ui.form.on('Employee', {
  refresh(frm) {
    if (frm.is_new()) return;
    frm.add_custom_button(__('Skill Gaps'), () => show_skill_gaps(frm), __('Development'));
    frm.add_custom_button(__('Development History'), () => show_history(frm), __('Development'));
    if (frappe.user_roles.includes('HR User') || frappe.user_roles.includes('HR Manager')) {
      frm.add_custom_button(__('Create Gap Actions'), () => create_gap_actions(frm), __('Development'));
    }
  }
});
function show_skill_gaps(frm){frappe.call({method:'qorg.qorg.employee_lifecycle.dev_api.gaps',args:{employee:frm.doc.name}}).then(r=>{const rows=(r.message||[]).map(x=>`<tr><td>${frappe.utils.escape_html(x.skill)}</td><td>${x.required_level}</td><td>${x.current_level}</td><td>${x.gap}</td><td>${x.compliant?__('Compliant'):__('Gap')}</td></tr>`).join('');frappe.msgprint({title:__('Skill Gaps'),message:`<table class="table table-bordered"><thead><tr><th>${__('Skill')}</th><th>${__('Required')}</th><th>${__('Current')}</th><th>${__('Gap')}</th><th>${__('Status')}</th></tr></thead><tbody>${rows}</tbody></table>`,wide:true});});}
function create_gap_actions(frm){frappe.prompt([{fieldname:'responsible_user',label:__('Responsible Person'),fieldtype:'Link',options:'User',reqd:1},{fieldname:'target_date',label:__('Target Date'),fieldtype:'Date',reqd:1}],v=>frappe.call({method:'qorg.qorg.employee_lifecycle.dev_api.gap_actions',args:{employee:frm.doc.name,responsible_user:v.responsible_user,target_date:v.target_date},freeze:true}).then(r=>frappe.msgprint(__('Created: {0}; existing: {1}',[(r.message.created||[]).length,(r.message.existing||[]).length]))),__('Create Skill-gap Actions'));}
function show_history(frm){frappe.call({method:'qorg.qorg.employee_lifecycle.dev_api.history',args:{employee:frm.doc.name},freeze:true}).then(r=>{const rows=(r.message||[]).map(x=>`<tr><td>${frappe.utils.escape_html(x.date||'')}</td><td>${frappe.utils.escape_html(x.doctype)}</td><td><a href="/app/${frappe.router.slug(x.doctype)}/${encodeURIComponent(x.name)}">${frappe.utils.escape_html(x.summary)}</a></td><td>${frappe.utils.escape_html(x.status||'')}</td></tr>`).join('');frappe.msgprint({title:__('Development and Performance History'),message:`<table class="table table-bordered"><thead><tr><th>${__('Date')}</th><th>${__('Type')}</th><th>${__('Record')}</th><th>${__('Status')}</th></tr></thead><tbody>${rows}</tbody></table>`,wide:true});});}
