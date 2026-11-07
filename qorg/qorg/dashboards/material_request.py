from erpnext.stock.doctype.material_request.material_request_dashboard import get_data as standard_get_data
from frappe import _
def get_data():
 data=standard_get_data();data.setdefault("non_standard_fieldnames",{})["Procurement Process"]="material_request";data.setdefault("transactions",[]).append({"label":_("QOrg Procurement"),"items":["Procurement Process"]});return data
