import frappe
from frappe import _
from frappe.model.document import Document

class AccountabilitySettings(Document):
    def validate(self):
        positive=("default_acknowledgement_days","default_triage_days","default_response_days","complex_response_days","update_frequency_days","intake_rate_limit_per_hour","tracking_rate_limit_per_hour","tracking_token_validity_days","anonymize_contact_after_days","disable_tracking_after_closure_days")
        for field in positive:
            if int(self.get(field) or 0) <= 0:
                frappe.throw(_("{0} must be greater than zero.").format(self.meta.get_label(field)))
        if int(self.complex_response_days) < int(self.default_response_days):
            frappe.throw(_("Complex Response Days cannot be less than Default Response Days."))
        if (self.enable_public_intake or self.enable_public_tracking) and self.require_captcha and not self.captcha_verifier_method:
            frappe.throw(_("CAPTCHA Verifier Method is required before enabling public intake or tracking."))
        if self.captcha_verifier_method:
            try: frappe.get_attr(self.captcha_verifier_method)
            except Exception: frappe.throw(_("CAPTCHA Verifier Method cannot be imported."))
