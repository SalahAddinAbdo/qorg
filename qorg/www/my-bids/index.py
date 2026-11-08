from qorg.qorg.portal_record_lists import get_portal_record_list_context


def get_context(context):
    return get_portal_record_list_context(context, "bids")
