import frappe
from qorg.qorg.procurement_contracting.communications import provision_email_templates
NOTIFICATIONS=[
 ('QOrg Procurement - Approved Purchase Request','Material Request',"doc.docstatus == 1 and doc.custom_procurement_method",'Approved Purchase Request | طلب شراء معتمد','owner','Approved request {{ doc.name }} requires procurement action.<hr><div dir="rtl">يتطلب طلب الشراء المعتمد {{ doc.name }} إجراء المشتريات.</div>'),
 ('QOrg Procurement - Process Setup Approved','Procurement Process',"doc.status == 'Setup Approved'",'Procurement Setup Approved | اعتماد إعداد عملية الشراء','owner','Process {{ doc.name }} setup was approved.<hr><div dir="rtl">تم اعتماد إعداد عملية الشراء {{ doc.name }}.</div>'),
 ('QOrg Procurement - Submission Received','Procurement Submission',"doc.submission_status == 'Submitted'",'Submission Received | تم استلام العرض','owner','Submission {{ doc.name }} was received.<hr><div dir="rtl">تم استلام العرض {{ doc.name }}.</div>'),
 ('QOrg Procurement - Technical Approved','Procurement Process',"doc.status == 'Technical Evaluation Approved'",'Technical Evaluation Approved | اعتماد التقييم الفني','owner','Technical evaluation is approved for {{ doc.name }}.<hr><div dir="rtl">تم اعتماد التقييم الفني للعملية {{ doc.name }}.</div>'),
 ('QOrg Procurement - Award Approved','Procurement Process',"doc.status == 'Award Approved'",'Award Approved | اعتماد الترسية','owner','Award is approved for {{ doc.name }}.<hr><div dir="rtl">تم اعتماد الترسية للعملية {{ doc.name }}.</div>'),
 ('QOrg Procurement - Contract Active','Procurement Contract',"doc.status == 'Active'",'Contract Activated | تفعيل العقد','owner','Contract {{ doc.name }} is active.<hr><div dir="rtl">تم تفعيل العقد {{ doc.name }}.</div>'),
]
def provision_notifications():
 provision_email_templates()
 for name,dt,condition,subject,receiver,message in NOTIFICATIONS:
  existing=frappe.db.exists('Notification',name); doc=frappe.get_doc('Notification',name) if existing else frappe.new_doc('Notification')
  doc.name=name; doc.subject=subject; doc.document_type=dt; doc.event='Save'; doc.condition=condition; doc.channel='Email'; doc.message=message; doc.enabled=1
  doc.set('recipients',[]); doc.append('recipients',{'receiver_by_document_field':receiver})
  doc.save(ignore_permissions=True) if existing else doc.insert(ignore_permissions=True)
