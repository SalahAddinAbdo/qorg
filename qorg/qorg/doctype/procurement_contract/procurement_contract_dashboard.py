from frappe import _
def get_data():
 return {"fieldname":"custom_procurement_contract","non_standard_fieldnames":{"Commitment Ledger":"procurement_process","Procurement Amendment":"procurement_process"},"transactions":[{"label":_("Procurement Control"),"items":["Commitment Ledger","Procurement Amendment"]},{"label":_("Standard Buying Documents"),"items":["Purchase Order","Purchase Receipt","Purchase Invoice"]}]}
