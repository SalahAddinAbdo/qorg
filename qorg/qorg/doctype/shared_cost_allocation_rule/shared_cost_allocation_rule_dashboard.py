from frappe import _


def get_data():
    return {
        "fieldname": "allocation_rule",
        "non_standard_fieldnames": {},
        "transactions": [
            {"label": _("Allocation"), "items": ["Shared Cost Allocation Run"]},
        ],
    }
