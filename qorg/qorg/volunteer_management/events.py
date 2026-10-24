from . import services


def validate_external_opportunity(doc, method=None):
    services.validate_opportunity(doc, method)
