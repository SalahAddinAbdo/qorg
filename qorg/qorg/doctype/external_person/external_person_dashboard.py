from __future__ import annotations


def get_data():
    return {
        "fieldname": "external_person",
        "non_standard_fieldnames": {
            "Job Applicant": "qorg_external_person",
        },
        "transactions": [
            {
                "label": "Applications",
                "items": ["Participation Application", "Job Applicant"],
            }
        ],
    }
