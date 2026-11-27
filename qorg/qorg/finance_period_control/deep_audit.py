import frappe
from qorg.qorg.finance_period_control.period_balances import COMMITMENT_STAGES

def run():
    checks=[]
    def add(name,count,details=None):checks.append({"check":name,"ok":count==0,"count":count,"details":details or []})
    duplicate=frappe.db.sql("select parent,event_key,count(*) qty from `tabCommitment Entry` where coalesce(event_key,'')!='' group by parent,event_key having count(*)>1",as_dict=True);add("Duplicate commitment event keys",len(duplicate),duplicate[:20])
    negative=frappe.db.sql("select parent,commitment_period,stage,sum(case when direction='Increase' then coalesce(base_amount,amount,0) else -coalesce(base_amount,amount,0) end) balance from `tabCommitment Entry` where stage in %s group by parent,commitment_period,stage having balance < -0.005",(COMMITMENT_STAGES,),as_dict=True);add("Negative stage balances",len(negative),negative[:20])
    overmatched=frappe.db.sql("select gl_entry,sum(matched_base_amount) matched,(select abs(debit-credit) from `tabGL Entry` where name=ce.gl_entry) gl_amount from `tabCommitment Entry` ce where coalesce(gl_entry,'')!='' group by gl_entry having matched-gl_amount>0.005",as_dict=True);add("GL entries matched above value",len(overmatched),overmatched[:20])
    missing_period=frappe.db.count("Commitment Entry",{"stage":["in",list(COMMITMENT_STAGES)],"commitment_period":["in",[None,""]]});add("Commitment events without period",missing_period)
    incomplete_distribution=frappe.db.sql("select name,parent from `tabCommitment Entry` where cost_distribution_row is not null and (project is null or budget_line is null or distribution_snapshot is null)",as_dict=True);add("Incomplete distribution snapshots",len(incomplete_distribution),incomplete_distribution[:20])
    return {"ready":all(x["ok"] for x in checks),"checks":checks}
@frappe.whitelist()
def execute():frappe.only_for(("System Manager","Accounts Manager"));return run()
