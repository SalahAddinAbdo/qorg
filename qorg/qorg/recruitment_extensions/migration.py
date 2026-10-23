import frappe
from .provisioning import provision_recruitment_extensions

def execute():
    provision_recruitment_extensions()
