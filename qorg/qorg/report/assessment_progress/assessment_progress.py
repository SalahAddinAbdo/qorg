import frappe

def _columns():
    columns=[{'label': 'Name', 'fieldname': 'name', 'fieldtype': 'Link', 'width': 170, 'options': 'Participation Assessment', 'sticky': True}, {'label': 'Application', 'fieldname': 'application', 'fieldtype': 'Link', 'width': 120, 'options': 'Participation Application', 'sticky': True}, {'label': 'Opportunity', 'fieldname': 'opportunity', 'fieldtype': 'Link', 'width': 170, 'options': 'External Opportunity', 'sticky': False}, {'label': 'Stage Name', 'fieldname': 'stage_name', 'fieldtype': 'Data', 'width': 120, 'sticky': False}, {'label': 'Attempt Number', 'fieldname': 'attempt_number', 'fieldtype': 'Int', 'width': 120, 'sticky': False}, {'label': 'Status', 'fieldname': 'status', 'fieldtype': 'Data', 'width': 120, 'sticky': False}, {'label': 'Score', 'fieldname': 'score', 'fieldtype': 'Percent', 'width': 120, 'sticky': False}, {'label': 'Result', 'fieldname': 'result', 'fieldtype': 'Data', 'width': 120, 'sticky': False}]
    return columns

def execute(filters=None):
    filters=filters or {}
    db_filters={}
    meta=frappe.get_meta('Participation Assessment')
    for key,value in filters.items():
        if value in (None,"",[]): continue
        if meta.has_field(key): db_filters[key]=["in",value] if isinstance(value,list) else value
    data=frappe.get_all('Participation Assessment',fields=['name', 'application', 'opportunity', 'stage_name', 'attempt_number', 'status', 'score', 'result'],filters=db_filters,order_by="modified desc")
    status_field="status" if meta.has_field("status") else None
    summary=[];chart=None
    if status_field:
        counts={}
        for row in data:
            label=row.get(status_field) or "Not Set";counts[label]=counts.get(label,0)+1
        summary=[{"value":len(data),"indicator":"Blue","label":"Total Records","datatype":"Int"}]+[{"value":v,"indicator":"Blue","label":k,"datatype":"Int"} for k,v in counts.items()]
        chart={"data":{"labels":list(counts),"datasets":[{"name":"Records","values":list(counts.values())}]},"type":"donut","height":260}
    return _columns(),data,None,chart,summary,1
