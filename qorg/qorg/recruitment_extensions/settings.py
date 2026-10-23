from frappe import _dict
from qorg.qorg.people_and_opportunities.settings import settings as people_settings

def get_settings(company=None):
    values=dict(people_settings(company))
    defaults={"screening_required":1,"minimum_screening_score":60,"minimum_interview_score":60,"offer_validity_days":10,"require_all_mandatory_interviews":1,"allow_reopen_decision":0,"require_evidence_notes":1,"require_complete_panel_feedback":1,"maximum_score_variance":25}
    for key,value in defaults.items():values.setdefault(key,value)
    return _dict(values)
