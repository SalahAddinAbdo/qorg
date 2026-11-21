import hashlib,json
def stable_hash(value): return hashlib.sha256(json.dumps(value,sort_keys=True,default=str,separators=(",",":")).encode()).hexdigest()
def rounded(value,precision=2): return round(float(value or 0),precision)
def payroll_source_fingerprint(frappe,payroll_entry):
    payroll=frappe.get_doc("Payroll Entry",payroll_entry);payload={"payroll_entry":{"name":payroll.name,"company":payroll.company,"start_date":payroll.start_date,"end_date":payroll.end_date,"posting_date":payroll.get("posting_date"),"currency":payroll.get("currency"),"exchange_rate":payroll.get("exchange_rate"),"modified":payroll.modified},"slips":[]}
    for name in frappe.get_all("Salary Slip",filters={"payroll_entry":payroll_entry,"docstatus":1},pluck="name",order_by="name"):
        doc=frappe.get_doc("Salary Slip",name);details=[]
        for table in ("earnings","deductions"):
            for row in doc.get(table) or []: details.append({"table":table,"idx":row.idx,"component":row.salary_component,"amount":row.amount,"additional_salary":row.get("additional_salary"),"statistical":row.get("is_statistical_component"),"taxable":row.get("is_tax_applicable"),"depends_on_payment_days":row.get("depends_on_payment_days"),"formula":row.get("formula"),"condition":row.get("condition")})
        payload["slips"].append({"name":doc.name,"employee":doc.employee,"modified":doc.modified,"gross_pay":doc.gross_pay,"total_deduction":doc.total_deduction,"net_pay":doc.net_pay,"currency":doc.get("currency"),"exchange_rate":doc.get("exchange_rate"),"payment_days":doc.get("payment_days"),"leave_without_pay":doc.get("leave_without_pay"),"details":details})
    return stable_hash(payload)
