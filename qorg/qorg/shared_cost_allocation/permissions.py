import frappe

def _query(doctype,user=None):
    user=user or frappe.session.user
    roles=set(frappe.get_roles(user))
    if roles.intersection({"System Manager","Accounts Manager","Shared Cost Allocation Manager"}): return ""
    companies=frappe.get_all("User Permission",filters={"user":user,"allow":"Company"},pluck="for_value")
    if not companies:return "1=0"
    return "`tab{}`.`company` in ({})".format(doctype,",".join(frappe.db.escape(x) for x in companies))
def allocation_query(user=None): return _query("Shared Cost Allocation Run",user)
def rule_query(user=None): return _query("Shared Cost Allocation Rule",user)
