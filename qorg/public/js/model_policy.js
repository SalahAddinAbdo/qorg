(() => {
 if (frappe.session.user === "Administrator") return;
 let policies={...(frappe.boot.qorg_action_policies||{})},observer,running=false;
 const scrub=v=>(v||"").toString().toLowerCase().replace(/[_\s]+/g,"-").replace(/[^a-z0-9-]/g,"").replace(/-+/g,"-").replace(/^-|-$/g,"");
 function dt(){if(window.cur_frm?.doctype)return cur_frm.doctype;if(window.cur_list?.doctype)return cur_list.doctype;const r=(frappe.get_route()||[]).map(scrub);return Object.keys(policies).find(x=>r.includes(scrub(x)))||null}
 function hide(e){if(e){e.classList.add("qorg-action-hidden");e.setAttribute("aria-hidden","true")}}
 function clear(){document.querySelectorAll(".qorg-action-hidden").forEach(e=>{e.classList.remove("qorg-action-hidden");e.removeAttribute("aria-hidden")})}
 function keep(e,c){const l=(e.textContent||e.getAttribute("data-label")||"").trim().toLowerCase();return (c.allow_print&&l.includes("print"))||(c.allow_email&&(l.includes("email")||l.includes("mail")))}
 function apply(){if(running)return;running=true;try{clear();const c=policies[dt()]||{policy:"Standard"};if(c.policy==="Standard")return;if(window.cur_frm){cur_frm.disable_save();cur_frm.page.clear_primary_action?.();cur_frm.page.clear_secondary_action?.()}document.querySelectorAll(".page-actions .btn-primary,.standard-actions .btn-primary,.grid-add-row,.tree-toolbar .btn-primary,.tree-node-toolbar .btn-primary").forEach(hide);if(c.policy==="View Only")document.querySelectorAll(".custom-actions .btn,.inner-toolbar .btn,.inner-group-button,.page-actions .btn,.standard-actions .btn,.menu-btn-group,.actions-btn-group,.dropdown-menu .dropdown-item").forEach(e=>{if(!keep(e,c))hide(e)});if(!c.allow_comments)document.querySelectorAll(".comment-box,.new-comment").forEach(hide);if(!c.allow_attachments)document.querySelectorAll(".attachments,.attachment-row,[data-label='Attachments']").forEach(hide)}finally{running=false}}
 function schedule(){apply();requestAnimationFrame(apply);[60,180,500,1200].forEach(x=>setTimeout(apply,x))}
 async function reload(){const r=await frappe.call({method:"qorg.qorg.enterprise_foundation.api.get_action_policies",silent:true});policies=r.message||{};frappe.boot.qorg_action_policies=policies;schedule()}
 observer=new MutationObserver(apply);observer.observe(document.body,{childList:true,subtree:true});frappe.router.on("change",schedule);frappe.realtime.on("qorg_model_policy_changed",reload);$(document).on("page-change form-refresh list-rendered",schedule);schedule();
})();
