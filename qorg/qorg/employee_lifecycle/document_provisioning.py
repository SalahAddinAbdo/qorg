import frappe

def provision_employee_documents():
    # The DocTypes are source-controlled. This hook provisions safe baseline document types only.
    examples = [
        ("Signed Employment Contract","CONTRACT","Contract",1,1),
        ("Identity Document","IDENTITY","Identity",1,1),
        ("Bank Account Confirmation","BANK","Financial",0,1),
        ("Confidentiality Agreement","CONFIDENTIALITY","Confidentiality",0,1),
        ("Safeguarding and PSEA Acknowledgement","PSEA","Safeguarding",0,1),
    ]
    if not frappe.db.exists("DocType","Employee Document Type"): return
    for name,code,category,expiry,verify in examples:
        if frappe.db.exists("Employee Document Type",name): continue
        frappe.get_doc({"doctype":"Employee Document Type","document_type_name":name,"document_code":code,"document_category":category,"applicable_subject_type":"Employee","has_issue_date":1,"has_expiry_date":expiry,"verification_required":verify,"storage_reference_required":1,"confidentiality_level":"Restricted HR" if category in {"Financial","Safeguarding"} else "Confidential","is_active":1}).insert(ignore_permissions=True)
