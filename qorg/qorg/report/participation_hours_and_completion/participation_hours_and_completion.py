import frappe

def _columns():
    columns=[{'label': 'Name', 'fieldname': 'name', 'fieldtype': 'Link', 'width': 170, 'options': 'Participation Engagement', 'sticky': True}, {'label': 'External Person', 'fieldname': 'external_person', 'fieldtype': 'Link', 'width': 170, 'options': 'External Person', 'sticky': True}, {'label': 'Participation Type', 'fieldname': 'participation_type', 'fieldtype': 'Data', 'width': 120, 'sticky': False}, {'label': 'Expected Hours', 'fieldname': 'expected_hours', 'fieldtype': 'Float', 'width': 120, 'sticky': False}, {'label': 'Completed Hours', 'fieldname': 'completed_hours', 'fieldtype': 'Float', 'width': 120, 'sticky': False}, {'label': 'Onboarding Completion', 'fieldname': 'onboarding_completion', 'fieldtype': 'Percent', 'width': 120, 'sticky': False}, {'label': 'Completion Status', 'fieldname': 'completion_status', 'fieldtype': 'Data', 'width': 120, 'sticky': False}]
    return columns

def execute(filters=None):
    filters=filters or {}
    db_filters={}
    meta=frappe.get_meta('Participation Engagement')
    for key,value in filters.items():
        if value in (None,"",[]): continue
        if meta.has_field(key): db_filters[key]=["in",value] if isinstance(value,list) else value
    data=frappe.get_all('Participation Engagement',fields=['name', 'external_person', 'participation_type', 'expected_hours', 'completed_hours', 'onboarding_completion', 'completion_status'],filters=db_filters,order_by="modified desc")
    status_field="status" if meta.has_field("status") else None
    summary=[];chart=None
    if status_field:
        counts={}
        for row in data:
            label=row.get(status_field) or "Not Set";counts[label]=counts.get(label,0)+1
        summary=[{"value":len(data),"indicator":"Blue","label":"Total Records","datatype":"Int"}]+[{"value":v,"indicator":"Blue","label":k,"datatype":"Int"} for k,v in counts.items()]
        chart={"data":{"labels":list(counts),"datasets":[{"name":"Records","values":list(counts.values())}]},"type":"donut","height":260}
    return _columns(),data,None,chart,summary,1
