import frappe

def _columns():
    columns=[{'label': 'Name', 'fieldname': 'name', 'fieldtype': 'Link', 'width': 170, 'options': 'Participation Application', 'sticky': True}, {'label': 'External Person', 'fieldname': 'external_person', 'fieldtype': 'Link', 'width': 170, 'options': 'External Person', 'sticky': True}, {'label': 'Opportunity', 'fieldname': 'opportunity', 'fieldtype': 'Link', 'width': 170, 'options': 'External Opportunity', 'sticky': False}, {'label': 'Participation Type', 'fieldname': 'participation_type', 'fieldtype': 'Data', 'width': 120, 'sticky': False}, {'label': 'Status', 'fieldname': 'status', 'fieldtype': 'Data', 'width': 120, 'sticky': False}, {'label': 'Screening Score', 'fieldname': 'screening_score', 'fieldtype': 'Percent', 'width': 120, 'sticky': False}, {'label': 'Assessment Score', 'fieldname': 'assessment_score', 'fieldtype': 'Percent', 'width': 120, 'sticky': False}, {'label': 'Overall Score', 'fieldname': 'overall_score', 'fieldtype': 'Percent', 'width': 120, 'sticky': False}, {'label': 'Ranking', 'fieldname': 'ranking', 'fieldtype': 'Int', 'width': 120, 'sticky': False}]
    return columns

def execute(filters=None):
    filters=filters or {}
    db_filters={}
    meta=frappe.get_meta('Participation Application')
    for key,value in filters.items():
        if value in (None,"",[]): continue
        if meta.has_field(key): db_filters[key]=["in",value] if isinstance(value,list) else value
    data=frappe.get_all('Participation Application',fields=['name', 'external_person', 'opportunity', 'participation_type', 'status', 'screening_score', 'assessment_score', 'overall_score', 'ranking'],filters=db_filters,order_by="modified desc")
    status_field="status" if meta.has_field("status") else None
    summary=[];chart=None
    if status_field:
        counts={}
        for row in data:
            label=row.get(status_field) or "Not Set";counts[label]=counts.get(label,0)+1
        summary=[{"value":len(data),"indicator":"Blue","label":"Total Records","datatype":"Int"}]+[{"value":v,"indicator":"Blue","label":k,"datatype":"Int"} for k,v in counts.items()]
        chart={"data":{"labels":list(counts),"datasets":[{"name":"Records","values":list(counts.values())}]},"type":"donut","height":260}
    return _columns(),data,None,chart,summary,1
