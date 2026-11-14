from qorg.qorg.procurement_contracting.communications import provision_email_templates


def provision_communications():
    provision_email_templates()
    from qorg.qorg.inventory_asset_custody.notifications import provision_notifications
    provision_notifications()
