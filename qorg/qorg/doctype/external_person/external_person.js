frappe.ui.form.on("External Person",{
 refresh(frm){
  apply_role_requirements(frm);
  if(!frm.is_new()&&!frm.doc.supplier&&frappe.model.can_create("Supplier"))frm.add_custom_button(__("Create Supplier Draft"),()=>frappe.call({method:"qorg.qorg.doctype.external_person.external_person.create_supplier_draft",args:{external_person:frm.doc.name},freeze:true,callback:r=>frappe.set_route("Form","Supplier",r.message)}),__("Create"));
 },
 external_roles:apply_role_requirements,
 identification_type(frm){frm.toggle_reqd("identification_number",Boolean(frm.doc.identification_type));}
});
function apply_role_requirements(frm){const professional=new Set(["Applicant","Individual Service Provider","Consultant","Trainer","Enumerator"]);const required=(frm.doc.external_roles||[]).some(r=>r.active&&professional.has(r.role_type));frm.toggle_reqd("professional_title",required);frm.toggle_reqd("professional_summary",required);}
