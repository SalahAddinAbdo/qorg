from frappe import _

def get_data():
    return {"fieldname":"custom_procurement_contract","non_standard_fieldnames":{"Commitment Ledger":"qorg_procurement_process","Contract Amendment":"contract","Procure Acceptance":"procurement_process"},"transactions":[{"label":_("Contract Governance"),"items":["Contract Amendment"]},{"label":_("Procurement Control"),"items":["Commitment Ledger","Procure Acceptance"]},{"label":_("Standard Buying Documents"),"items":["Purchase Order","Purchase Receipt","Purchase Invoice"]}]}
