import frappe
from frappe.utils import flt,getdate,nowdate
from .classification import resolve_procurement_type
from .policy_engine import PolicyContext,PolicyRule,resolve_policy
from qorg.qorg.procurement_contracting.settings import get_setting
class MaterialRequestProcurementMixin:
 def validate(self):
  super().validate()
  if self.material_request_type!='Purchase' or not True: return
  if not get_setting('enable_extended_procurement'): return
  if frappe.db.exists('DocType','Company Feature Settings'):
   enabled=frappe.db.get_value('Company Feature Settings',{'company':self.company},'extended_procurement')
   if enabled is not None and not int(enabled or 0): return
  total=sum(flt(getattr(r,'custom_estimated_amount',0)) for r in self.items)
  ctx=PolicyContext(self.company,frappe.get_cached_value('Company',self.company,'default_currency'),self.get('custom_procurement_type') or resolve_procurement_type(self.items),total,getdate(self.transaction_date or nowdate()),project=self.get('project'))
  rules=[PolicyRule(r.name,r.company,r.currency,r.procurement_type,r.minimum_amount,r.maximum_amount,r.procurement_method,r.priority,r.effective_from,r.effective_to,r.risk_level,r.project,None,None,r.emergency_only,False,{}) for r in frappe.get_all('Procurement Policy Rule',filters={'docstatus':1,'disabled':0},fields=['*'])]
  result=resolve_policy(ctx,rules); method=frappe.get_doc('Procurement Method',result['method'])
  self.custom_estimated_procurement_value=total; self.custom_procurement_policy_rule=result['rule']; self.custom_procurement_method=result['method']; self.custom_requires_procurement_process=method.requires_procurement_process
  self.custom_procurement_next_action='Create Procurement Process' if method.requires_procurement_process else ('Create RFQ' if method.uses_standard_rfq else 'Create Purchase Order')
  self.custom_minimum_quotations = method.default_minimum_quotations or 0
  self.custom_requires_public_notice = method.requires_public_notice
  self.custom_requires_opening_committee = method.requires_opening_committee
  self.custom_requires_technical_evaluation = method.requires_technical_evaluation
  self.custom_requires_financial_evaluation = method.requires_financial_evaluation
  self.custom_requires_two_envelope = method.requires_two_envelope
  self.custom_technical_weight = method.default_technical_weight or 0
  self.custom_financial_weight = method.default_financial_weight or 0
  self.custom_technical_threshold = method.default_technical_threshold or 0
  self.custom_requires_contract = method.requires_procurement_process
