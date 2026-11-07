from frappe import _
def get_data():
 return {"fieldname":"procurement_process","transactions":[{"label":_("Publication and Bids"),"items":["Procurement Notice","Procurement Submission","Procurement Bid Opening","Bid Precheck"]},{"label":_("Evaluation and Award"),"items":["Technical Evaluation","Financial Evaluation","Evaluation Summary","Award Recommendation","Award Decision"]},{"label":_("Contracting"),"items":["Procurement Contract","Commitment Ledger","Procurement Amendment","Procurement Clarification","Procurement Complaint"]}]}
