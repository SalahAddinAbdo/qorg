import frappe
from frappe import _
from .evaluation_engine import individual_average, weighted_member_average, consensus_score, individual_then_consensus, financial_score, weighted_result

def calculate_technical(doc):
    process=frappe.get_doc("Procurement Process",doc.procurement_process)
    by_criterion={}
    for row in doc.scores:
        by_criterion.setdefault(row.criterion,[]).append(row.as_dict())
    criteria={r.criterion:r for r in process.criteria if r.component=="Technical"}
    total=0
    for name, criterion in criteria.items():
        rows=by_criterion.get(name,[]); method=criterion.scoring_method
        if method=="Individual Average": raw=individual_average(rows)
        elif method=="Weighted Member Average": raw=weighted_member_average(rows)
        elif method=="Consensus Score":
            row=next((r for r in rows if r.get("submitted") and not r.get("excluded")),None)
            if not row: frappe.throw(_("Consensus score is missing for {0}").format(name))
            raw=consensus_score(row["score"],1,row.get("remarks"))
        elif method=="Individual then Consensus":
            consensus=next((r for r in rows if r.get("evaluator")=="Consensus"),None)
            if not consensus: frappe.throw(_("Consensus result is missing for {0}").format(name))
            raw=individual_then_consensus([r for r in rows if r.get("evaluator")!="Consensus"],consensus["score"],1,consensus.get("remarks"))["consensus"]
        elif method in ("Individual Pass Fail","Consensus Pass Fail"):
            if any(r.get("decision")=="Fail" for r in rows): doc.result="Failed"; raw=0
            else: raw=criterion.maximum_score or 100
        else:
            row=next((r for r in rows if r.get("submitted") and not r.get("excluded")),None); raw=(row or {}).get("score",0)
        max_score=criterion.maximum_score or 100
        normalized=float(raw)/float(max_score)*100
        total += float(weighted_result(normalized,criterion.weight or 0))
    doc.raw_technical_score=total
    doc.result="Passed" if total >= (doc.technical_threshold or process.technical_threshold or 0) else "Failed"

def calculate_financial(doc):
    doc.evaluated_price=(doc.original_price or 0)+(doc.arithmetic_corrections or 0)+(doc.taxes or 0)+(doc.other_evaluated_costs or 0)-(doc.discounts or 0)
    if doc.lowest_evaluated_price and doc.evaluated_price:
        doc.financial_score=financial_score(doc.lowest_evaluated_price,doc.evaluated_price)

def rebuild_summary(process_name):
    process=frappe.get_doc("Procurement Process",process_name)
    name=frappe.db.get_value("Procurement Evaluation Summary",{"procurement_process":process.name})
    summary=frappe.get_doc("Procurement Evaluation Summary",name) if name else frappe.new_doc("Procurement Evaluation Summary")
    summary.procurement_process=process.name; summary.technical_weight=process.technical_weight; summary.financial_weight=process.financial_weight; summary.set("rows",[])
    submissions=frappe.get_all("Procurement Submission",filters={"procurement_process":process.name,"docstatus":1},fields=["name","supplier"])
    for sub in submissions:
        tech=frappe.db.get_value("Procurement Technical Evaluation",{"submission":sub.name,"docstatus":1},["raw_technical_score","result"],as_dict=True) or {}
        fin=frappe.db.get_value("Procurement Financial Evaluation",{"submission":sub.name,"docstatus":1},["evaluated_price","financial_score"],as_dict=True) or {}
        tw=float(weighted_result(tech.get("raw_technical_score",0),process.technical_weight or 0)); fw=float(weighted_result(fin.get("financial_score",0),process.financial_weight or 0))
        summary.append("rows",{"supplier":sub.supplier,"submission":sub.name,"preliminary_result":"Responsive","technical_score":tech.get("raw_technical_score",0),"technical_weighted":tw,"evaluated_price":fin.get("evaluated_price",0),"financial_score":fin.get("financial_score",0),"financial_weighted":fw,"total_score":tw+fw})
    ordered=sorted(summary.rows,key=lambda r:(-(r.total_score or 0),r.evaluated_price or 0))
    for rank,row in enumerate(ordered,1): row.rank=rank; row.recommendation="Recommended" if rank==1 else "Reserve"
    summary.recommended_supplier=ordered[0].supplier if ordered else None
    summary.save(ignore_permissions=True)
    return summary.name
