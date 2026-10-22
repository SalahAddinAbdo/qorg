async function qorg_load_project_team(frm){frm.__project_team=[];if(!frm.doc.project)return;const r=await frappe.call({method:"qorg.qorg.project_management.api.get_project_team_employees",args:{project:frm.doc.project}});frm.__project_team=r.message||[];}
function qorg_team_query(frm){const e=frm.__project_team||[];return{filters:[["Employee","status","=","Active"],["Employee","name",e.length?"in":"=",e.length?e:"__none__"]]};}

frappe.ui.form.on("Project Beneficiary Plan",{setup(frm){frm.__project_team=[];qorg_set_queries(frm);},async onload(frm){await qorg_load_project_team(frm);qorg_set_queries(frm);},async refresh(frm){await qorg_load_project_team(frm);qorg_set_queries(frm);},async project(frm){await qorg_load_project_team(frm);qorg_set_queries(frm);}});
function qorg_set_queries(frm){}
