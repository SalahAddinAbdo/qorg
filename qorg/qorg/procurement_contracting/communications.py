import frappe
from frappe import _
from frappe.utils.jinja import render_template

SPECS={
"Approved Purchase Request":("Approved Purchase Request | طلب شراء معتمد","An approved purchase request requires procurement action under the selected policy and method.","يتطلب طلب الشراء المعتمد إجراء مشتريات وفقا للسياسة والطريقة المحددتين.","Review and start the permitted route.","راجع الطلب وابدأ المسار المسموح."),
"Procurement Process Assignment":("Procurement Process Assignment | تكليف بعملية مشتريات","A procurement process has been assigned for setup and follow-up.","تم تكليفكم بإعداد ومتابعة عملية مشتريات.","Review the policy snapshot, committees and timetable.","راجع ملخص السياسة واللجان والجدول الزمني."),
"Procurement Invitation":("Invitation to Participate | دعوة للمشاركة","You are invited to review the published procurement documents and submit a complete offer before closing.","ندعوكم لمراجعة وثائق المنافسة وتقديم عرض مكتمل قبل الإغلاق.","Open the opportunity and submit through the supplier portal.","افتح الفرصة وقدم العرض عبر بوابة الموردين."),
"Submission Deadline Reminder":("Submission Deadline Reminder | تذكير بموعد الإغلاق","The published submission deadline is approaching.","يقترب موعد إغلاق التقديم المنشور.","Complete and submit the offer before the deadline.","استكمل العرض وقدمه قبل الموعد النهائي."),
"Bid Submission Receipt":("Submission Receipt | إشعار استلام العرض","The submission was received and registered successfully.","تم استلام العرض وتسجيله بنجاح.","Keep the reference below for future communication.","احتفظ بالمرجع أدناه للمراسلات اللاحقة."),
"Supplier Information Request":("Additional Information Required | مطلوب معلومات إضافية","Additional supplier information or evidence is required.","يلزم تقديم معلومات أو أدلة إضافية عن المورد.","Open the supplier Web Form and resubmit the requested information.","افتح نموذج المورد وأعد تقديم المعلومات المطلوبة."),
"Supplier Profile Approved":("Supplier Profile Approved | اعتماد ملف المورد","The supplier profile passed the required due-diligence review.","اجتاز ملف المورد مراجعة العناية الواجبة المطلوبة.","The profile may now be used for eligible procurement participation.","يمكن استخدام الملف للمشاركة في المشتريات المؤهلة."),
"Supplier Profile Rejected":("Supplier Profile Decision | قرار ملف المورد","The supplier profile was not approved under the current review.","لم يتم اعتماد ملف المورد في المراجعة الحالية.","Review the recorded reasons and contact procurement if clarification is needed.","راجع الأسباب المسجلة وتواصل مع المشتريات عند الحاجة."),
"Bid Opening Completed":("Bid Opening Completed | اكتمال فتح العطاءات","The formal bid-opening stage is complete.","اكتملت مرحلة فتح العطاءات رسميا.","Proceed with the approved preliminary examination.","انتقل إلى الفحص الأولي المعتمد."),
"Technical Evaluation Assignment":("Technical Evaluation Assignment | تكليف بالتقييم الفني","A technical evaluation has been assigned.","تم تكليفكم بإجراء تقييم فني.","Complete individual scoring and evidence within the timetable.","استكمل الدرجات الفردية والأدلة ضمن الجدول."),
"Technical Evaluation Approved":("Technical Evaluation Approved | اعتماد التقييم الفني","The technical evaluation is approved.","تم اعتماد التقييم الفني.","Authorized financial evaluators may proceed.","يمكن للمقيمين الماليين المخولين المتابعة."),
"Financial Evaluation Ready":("Financial Evaluation Ready | جاهزية التقييم المالي","The financial stage is ready after technical approval.","أصبحت المرحلة المالية جاهزة بعد اعتماد الفني.","Authorized committee members should complete financial evaluation.","على أعضاء اللجنة المخولين استكمال التقييم المالي."),
"Award Recommendation Submitted":("Award Recommendation Submitted | تقديم توصية الترسية","The award recommendation was submitted for decision.","تم تقديم توصية الترسية لاتخاذ القرار.","Review ranking, rationale and any deviation before approval.","راجع الترتيب والمبررات وأي انحراف قبل الاعتماد."),
"Award Notification":("Award Decision | قرار الترسية","The approved procurement award decision is available.","أصبح قرار الترسية المعتمد متاحا.","Review the official decision and next contractual steps.","راجع القرار الرسمي والخطوات التعاقدية التالية."),
"Unsuccessful Bidder Notice":("Procurement Result | نتيجة المنافسة","Thank you for participating. The submission was not selected.","شكرا لمشاركتكم. لم يتم اختيار العرض.","Use the official clarification or complaint route when applicable.","استخدم مسار التوضيح أو الشكوى الرسمي عند انطباقه."),
"Contract Approval Required":("Contract Approval Required | مطلوب اعتماد العقد","A procurement contract requires review and approval.","يتطلب عقد مشتريات المراجعة والاعتماد.","Verify scope, value, supplier, dates, milestones and guarantees.","تحقق من النطاق والقيمة والمورد والتواريخ والمراحل والضمانات."),
"Contract Activated":("Contract Activated | تفعيل العقد","The procurement contract is active.","تم تفعيل عقد المشتريات.","Monitor milestones, guarantees, commitments, acceptance and expiry.","تابع المراحل والضمانات والالتزامات والاستلام والانتهاء."),
"Contract Expiry Reminder":("Contract Expiry Reminder | تذكير بانتهاء العقد","The contract expiry date is approaching.","يقترب تاريخ انتهاء العقد.","Review completion, extension, obligations and closure requirements.","راجع الإنجاز والتمديد والالتزامات ومتطلبات الإغلاق."),
"Guarantee Expiry Reminder":("Guarantee Expiry Reminder | تذكير بانتهاء الضمان","A procurement guarantee is approaching expiry.","يقترب انتهاء ضمان مشتريات.","Confirm renewal, release or enforcement before expiry.","أكد التجديد أو الإفراج أو التنفيذ قبل الانتهاء."),
"Contract Milestone Reminder":("Contract Milestone Reminder | تذكير بمرحلة تعاقدية","A contract milestone is approaching or overdue.","تقترب مرحلة تعاقدية أو أصبحت متأخرة.","Review deliverables, evidence, acceptance and payment linkage.","راجع المخرجات والأدلة والاستلام والارتباط بالدفع."),
"Procurement Complaint Acknowledgement":("Complaint Acknowledgement | إشعار استلام الشكوى","The procurement complaint was received and registered.","تم استلام شكوى المشتريات وتسجيلها.","The complaint will be reviewed under the applicable procedure.","ستراجع الشكوى وفق الإجراء المعتمد."),
"Procurement Clarification Response":("Procurement Clarification | توضيح مشتريات","An official clarification response is available.","أصبح رد التوضيح الرسمي متاحا.","Review the response and published procurement information.","راجع الرد ومعلومات المشتريات المنشورة."),
}

def _body(subject,en,ar,action_en,action_ar):
 return f"""<div style='font-family:Arial,sans-serif;max-width:760px;margin:auto;border:1px solid #d9e2e8;border-radius:10px;overflow:hidden'><div style='padding:16px 24px;background:{{{{ frappe.db.get_value("Company", doc.company, "custom_primary_color") or "#137690" if doc.get("company") else "#137690" }}}};color:#fff'><table width='100%'><tr><td>{{% if doc.get("company") %}}{{{{ frappe.db.get_value("Company", doc.company, "company_logo") or "" }}}}{{% endif %}}</td><td align='right'><b>{subject}</b></td></tr></table></div><div style='padding:26px;line-height:1.75'><p>Dear Recipient,</p><p>{en}</p><div style='border-left:4px solid #CBAE66;background:#f7f9fb;padding:14px'><b>Reference:</b> {{{{ doc.name }}}}<br><b>Title:</b> {{{{ doc.title or doc.contract_title or doc.legal_name or '' }}}}<br><b>Company / Project:</b> {{{{ doc.company or '' }}}} / {{{{ doc.project or '' }}}}<br><b>Status:</b> {{{{ doc.status or doc.workflow_state or doc.submission_status or doc.registration_status or '' }}}}<br><b>Deadline:</b> {{{{ doc.deadline or doc.submission_deadline or doc.end_date or doc.valid_to or '' }}}}<br><b>Required action:</b> {action_en}</div><hr><div dir='rtl' style='text-align:right'><p>السيد/السيدة المستلم المحترم،</p><p>{ar}</p><div style='border-right:4px solid #CBAE66;background:#f7f9fb;padding:14px'><b>المرجع:</b> {{{{ doc.name }}}}<br><b>العنوان:</b> {{{{ doc.title or doc.contract_title or doc.legal_name or '' }}}}<br><b>الشركة / المشروع:</b> {{{{ doc.company or '' }}}} / {{{{ doc.project or '' }}}}<br><b>الحالة:</b> {{{{ doc.status or doc.workflow_state or doc.submission_status or doc.registration_status or '' }}}}<br><b>الموعد:</b> {{{{ doc.deadline or doc.submission_deadline or doc.end_date or doc.valid_to or '' }}}}<br><b>الإجراء المطلوب:</b> {action_ar}</div></div><p style='margin-top:22px'><a href='{{{{ qorg_link or frappe.utils.get_url_to_form(doc.doctype, doc.name) }}}}' style='background:#137690;color:#fff;text-decoration:none;padding:11px 18px;border-radius:5px'>Open | فتح</a></p><p style='font-size:12px;color:#667085'>Official QOrg communication. Do not forward confidential procurement information.<br>مراسلة رسمية من QOrg. يمنع إعادة توجيه معلومات المشتريات السرية.</p></div></div>"""
TEMPLATES={name:{"subject":subject,"body":_body(subject,en,ar,aen,aar)} for name,(subject,en,ar,aen,aar) in SPECS.items()}

def provision_email_templates():
 for name,spec in TEMPLATES.items():
  existing=frappe.db.exists("Email Template",name);doc=frappe.get_doc("Email Template",name) if existing else frappe.new_doc("Email Template")
  doc.name=name;doc.subject=spec["subject"];doc.response=spec["body"];doc.use_html=1
  doc.save(ignore_permissions=True) if existing else doc.insert(ignore_permissions=True)

def _portal_link(doc):
 if doc.doctype=="Supplier Registration":return frappe.utils.get_url(f"/supplier-registration/{doc.name}")
 if doc.doctype=="Procurement Submission":return frappe.utils.get_url(f"/tender-submission/{doc.name}")
 if doc.doctype=="Procurement Notice":return frappe.utils.get_url(f"/procurement-opportunity?route={doc.route}")
 return frappe.utils.get_url_to_form(doc.doctype,doc.name)

@frappe.whitelist()
def preview_template(reference_doctype,reference_name,template_name):
 frappe.has_permission(reference_doctype,"read",reference_name,throw=True);doc=frappe.get_doc(reference_doctype,reference_name);template=frappe.get_doc("Email Template",template_name);ctx={"doc":doc,"qorg_link":_portal_link(doc)}
 return {"subject":render_template(template.subject or "",ctx),"message":render_template(template.response or "",ctx)}

@frappe.whitelist()
def send_template(reference_doctype,reference_name,template_name,recipients,cc=None):
 frappe.has_permission(reference_doctype,"read",reference_name,throw=True)
 if isinstance(recipients,str):recipients=[x.strip() for x in recipients.replace(";",",").split(",") if x.strip()]
 if not recipients:frappe.throw(_("At least one recipient is required."))
 preview=preview_template(reference_doctype,reference_name,template_name);frappe.sendmail(recipients=recipients,cc=cc or None,subject=preview["subject"],message=preview["message"],reference_doctype=reference_doctype,reference_name=reference_name)
 return {"sent":True,"recipients":recipients}
