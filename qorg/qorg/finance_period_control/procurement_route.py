import frappe
from frappe import _
from frappe.utils import now_datetime
EXCEPTION_MODES={"Direct","Single Source","Emergency"}

def _method(name):return frappe.db.get_value("Procurement Method",name,["procurement_mode","requires_procurement_process","allows_direct_purchase_order"],as_dict=True) if name else frappe._dict()
def _mr_names(doc):return sorted({r.get("material_request") for r in doc.items if r.get("material_request")})
def _po_names(doc):return sorted({r.get("purchase_order") for r in doc.items if r.get("purchase_order")})
def _all_linked(doc,kind):
 flags=[bool(r.get("material_request") or r.get("material_request_item")) if kind=="PO" else bool(r.get("purchase_order") or r.get("po_detail")) for r in doc.items]
 if any(flags) and not all(flags):frappe.throw(_("Linked and standalone rows cannot be combined in one {0}.").format(doc.doctype))
 return bool(flags and all(flags))
def _apply(doc,values):
 for k,v in values.items():doc.set(k,v)
def validate_material_request(doc,method=None):
 if doc.material_request_type!="Purchase":return
 method_name=doc.get("custom_procurement_method")
 if not method_name:frappe.throw(_("Procurement Method is required for a Purchase Material Request."))
 spec=_method(method_name);exception=spec.procurement_mode in EXCEPTION_MODES
 if exception:
  if not doc.qorg_route_reason:frappe.throw(_("Exception Reason is required for this procurement method."))
  if not doc.qorg_route_approval_reference:frappe.throw(_("Approval Reference is required for this procurement method."))
  if doc.qorg_route_approval_status not in ("Approved","Rejected"):doc.qorg_route_approval_status="Pending"
 else:doc.qorg_route_approval_status="Not Required"
def validate_purchase_order(doc,method=None):
 linked=_all_linked(doc,"PO")
 if linked:
  mrs=_mr_names(doc)
  methods={frappe.db.get_value("Material Request",x,"custom_procurement_method") for x in mrs}
  if len(methods)!=1:frappe.throw(_("All Material Requests in a Purchase Order must use the same Procurement Method."))
  method_name=methods.pop();spec=_method(method_name)
  processes=frappe.get_all("Procurement Process",filters={"material_request":["in",mrs],"docstatus":["<",2]},fields=["name","status","procurement_method"])
  if len(processes)>1:frappe.throw(_("The Purchase Order cannot combine more than one Procurement Process."))
  process=frappe._dict(processes[0]) if processes else frappe._dict()
  if process and process.procurement_method and process.procurement_method!=method_name:frappe.throw(_("Procurement Process method does not match the Material Request method."))
  mr_statuses={frappe.db.get_value("Material Request",x,"qorg_route_approval_status") for x in mrs}
  if spec.procurement_mode in EXCEPTION_MODES:
   if mr_statuses!={"Approved"}:frappe.throw(_("The exception procurement route must be approved on the Material Request before creating the Purchase Order."))
  elif spec.requires_procurement_process:
   if not process or process.status!="Award Approved":frappe.throw(_("The Procurement Process must reach Award Approved before the Purchase Order can be submitted."))
  award=frappe.db.get_value("Award Decision",{"procurement_process":process.name,"decision":"Approved","docstatus":1},"name") if process else None
  if process and process.status=="Award Approved" and not award:frappe.throw(_("An approved submitted Award Decision is required before the Purchase Order."))
  mr=frappe.get_doc("Material Request",mrs[0]);_apply(doc,{"qorg_procurement_method":method_name,"qorg_route_source":"Award Decision" if award else ("Procurement Process" if process else "Material Request"),"qorg_route_inherited":1,"qorg_procurement_process":process.name if process else None,"qorg_award_decision":award,"qorg_route_approval_status":"Approved" if process else mr.qorg_route_approval_status,"qorg_route_reason":mr.qorg_route_reason,"qorg_route_approval_reference":mr.qorg_route_approval_reference,"qorg_route_approved_by":mr.qorg_route_approved_by,"qorg_route_approved_on":mr.qorg_route_approved_on})
 else:
  method_name=doc.qorg_procurement_method;spec=_method(method_name)
  if not method_name or spec.procurement_mode not in EXCEPTION_MODES or not spec.allows_direct_purchase_order:frappe.throw(_("Standalone Purchase Orders require an approved Direct, Single Source, or Emergency Procurement Method that allows direct Purchase Orders."))
  _apply(doc,{"qorg_procurement_method":method_name,"qorg_route_source":"Standalone Document","qorg_route_inherited":0,"qorg_route_approval_status":doc.qorg_route_approval_status or "Pending","qorg_route_reason":doc.qorg_route_reason,"qorg_route_approval_reference":doc.qorg_route_approval_reference})
  missing=[str(r.idx) for r in doc.items if not (r.get("project") or doc.get("project")) or not r.get("budget_line")]
  if missing:frappe.throw(_("Project and Budget Line are required for standalone Purchase Order rows: {0}").format(", ".join(missing)))
  if not doc.qorg_route_reason or not doc.qorg_route_approval_reference:frappe.throw(_("Standalone Purchase Orders require an Exception Reason and Approval Reference."))
  if doc.docstatus==1 and doc.qorg_route_approval_status!="Approved":frappe.throw(_("Standalone Purchase Order route must be approved before submission."))
def validate_purchase_invoice(doc,method=None):
 if doc.get("is_return"):return
 linked=_all_linked(doc,"PI")
 if linked:
  pos=_po_names(doc)
  routes=[frappe.db.get_value("Purchase Order",x,["qorg_procurement_method","qorg_procurement_process","qorg_award_decision","qorg_route_approval_status","qorg_route_reason","qorg_route_approval_reference","qorg_route_approved_by","qorg_route_approved_on"],as_dict=True) for x in pos]
  if len({x.qorg_procurement_method for x in routes})!=1:frappe.throw(_("All Purchase Orders in a Purchase Invoice must use the same Procurement Method."))
  x=routes[0];_apply(doc,{"qorg_procurement_method":x.qorg_procurement_method,"qorg_route_source":"Purchase Order","qorg_route_inherited":1,"qorg_procurement_process":x.qorg_procurement_process,"qorg_award_decision":x.qorg_award_decision,"qorg_route_approval_status":x.qorg_route_approval_status,"qorg_route_reason":x.qorg_route_reason,"qorg_route_approval_reference":x.qorg_route_approval_reference,"qorg_route_approved_by":x.qorg_route_approved_by,"qorg_route_approved_on":x.qorg_route_approved_on})
 else:
  method_name=doc.qorg_procurement_method;spec=_method(method_name)
  if not method_name or spec.procurement_mode not in EXCEPTION_MODES:frappe.throw(_("Standalone Purchase Invoices require a Direct, Single Source, or Emergency Procurement Method."))
  _apply(doc,{"qorg_procurement_method":method_name,"qorg_route_source":"Standalone Document","qorg_route_inherited":0,"qorg_route_approval_status":doc.qorg_route_approval_status or "Pending","qorg_route_reason":doc.qorg_route_reason,"qorg_route_approval_reference":doc.qorg_route_approval_reference})
  missing=[str(r.idx) for r in doc.items if not (r.get("project") or doc.get("project")) or not r.get("budget_line")]
  if missing:frappe.throw(_("Project and Budget Line are required for standalone Purchase Invoice rows: {0}").format(", ".join(missing)))
  if not doc.qorg_route_reason or not doc.qorg_route_approval_reference:frappe.throw(_("Standalone Purchase Invoices require an Exception Reason and Approval Reference."))
  if doc.docstatus==1 and doc.qorg_route_approval_status!="Approved":frappe.throw(_("Standalone Purchase Invoice route must be approved before submission."))
def validate(doc,method=None):
 if doc.doctype=="Material Request":return validate_material_request(doc,method)
 if doc.doctype=="Purchase Order":return validate_purchase_order(doc,method)
 if doc.doctype=="Purchase Invoice":return validate_purchase_invoice(doc,method)
@frappe.whitelist()
def decide(doctype,name,decision):
 frappe.only_for(("Procurement Manager","Procurement Award Approver","System Manager"))
 if doctype not in ("Material Request","Purchase Order","Purchase Invoice") or decision not in ("Approved","Rejected"):frappe.throw(_("Invalid route approval decision."))
 doc=frappe.get_doc(doctype,name);doc.check_permission("write")
 if not doc.qorg_route_reason or not doc.qorg_route_approval_reference:frappe.throw(_("Exception Reason and Approval Reference are required."))
 doc.db_set("qorg_route_approval_status",decision);doc.db_set("qorg_route_approved_by",frappe.session.user);doc.db_set("qorg_route_approved_on",now_datetime());return {"status":decision}
