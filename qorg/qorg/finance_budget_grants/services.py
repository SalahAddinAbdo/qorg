from __future__ import annotations
import frappe
from frappe import _
from frappe.utils import flt, getdate

INHERITED_FIELDS=("funding_agreement","cost_category","allow_budget_transfer","flexibility_percent","eligibility_start_date","eligibility_end_date")

def settings():
 d={"flexibility":10,"block":1,"require_agreement":1,"eligibility":1}
 if not frappe.db.exists("DocType","Projects Settings"): return d
 s=frappe.get_cached_doc("Projects Settings")
 d.update(flexibility=flt(s.get("custom_default_budget_flexibility_percent") or 10),block=int(s.get("custom_block_budget_overrun") or 0),require_agreement=int(s.get("custom_require_funding_agreement") or 0),eligibility=int(s.get("custom_enforce_eligibility_period") or 0))
 return d

def _project_funding_rows(project):
 if not project or not frappe.db.exists("Project",project): return []
 meta=frappe.get_meta("Project")
 field=meta.get_field("custom_funding_sources")
 if not field or field.options!="Project Funding Source": return []
 return frappe.get_all("Project Funding Source",filters={"parent":project,"parenttype":"Project","parentfield":"custom_funding_sources"},fields=["name","donor","is_primary_donor","funding_status","funding_agreement","cost_category","allow_budget_transfer","flexibility_percent","eligibility_start_date","eligibility_end_date","funding_start_date","funding_end_date"],order_by="is_primary_donor desc, idx asc")

def _select_source(project, agreement=None):
    """Return one deterministic Project Funding Source for Budget Line defaults.

    A manually selected agreement always wins.  Otherwise the unique primary donor
    row that carries an agreement is authoritative, irrespective of whether the
    funding pipeline status is Potential, Approved, or Partially Approved.  The
    status describes the funding lifecycle; it must not hide an agreement already
    linked to the project's designated primary donor.
    """
    rows = _project_funding_rows(project)
    if not rows:
        return None

    if agreement:
        matches = [row for row in rows if row.funding_agreement == agreement]
        return matches[0] if len(matches) == 1 else None

    rows_with_agreement = [row for row in rows if row.funding_agreement]
    primary_with_agreement = [row for row in rows_with_agreement if row.is_primary_donor]
    if len(primary_with_agreement) == 1:
        return primary_with_agreement[0]
    if len(primary_with_agreement) > 1:
        return None

    approved_with_agreement = [
        row for row in rows_with_agreement
        if row.funding_status in ("Approved", "Partially Approved")
    ]
    if len(approved_with_agreement) == 1:
        return approved_with_agreement[0]
    if len(rows_with_agreement) == 1:
        return rows_with_agreement[0]

    approved = [
        row for row in rows
        if row.funding_status in ("Approved", "Partially Approved")
    ]
    primary = [row for row in approved if row.is_primary_donor]
    if len(primary) == 1:
        return primary[0]
    if len(approved) == 1:
        return approved[0]
    return None

@frappe.whitelist()
def get_budget_line_finance_defaults(project, funding_agreement=None):
 row=_select_source(project,funding_agreement)
 if not row:return {}
 return {"project_funding_source_row":row.name,"source_donor":row.donor,"funding_agreement":row.funding_agreement,"cost_category":row.cost_category or "Direct Cost","allow_budget_transfer":int(row.allow_budget_transfer or 0),"flexibility_percent":flt(row.flexibility_percent if row.flexibility_percent is not None else settings()["flexibility"]),"eligibility_start_date":row.eligibility_start_date or row.funding_start_date,"eligibility_end_date":row.eligibility_end_date or row.funding_end_date}

def apply_budget_line_defaults(doc,method=None):
 if not doc.get("project") or doc.get("is_group") or doc.get("finance_values_overridden"): return
 values=get_budget_line_finance_defaults(doc.project,doc.get("funding_agreement"))
 if not values:return
 for field,value in values.items():
  if not doc.get(field): doc.set(field,value)

def validate_project_funding_source(parent,method=None):
 rows=parent.get("custom_funding_sources") or []
 primaries=[r for r in rows if r.is_primary_donor and r.funding_status in ("Approved","Partially Approved")]
 if len(primaries)>1: frappe.throw(_("Only one approved Project Funding Source can be marked as Primary Donor."))
 for row in rows:
  if row.eligibility_start_date and row.eligibility_end_date and getdate(row.eligibility_start_date)>getdate(row.eligibility_end_date): frappe.throw(_("Funding source eligibility start date cannot be after end date."))
  if not 0<=flt(row.flexibility_percent)<=100: frappe.throw(_("Funding source flexibility must be between 0 and 100%."))
  if row.funding_agreement:
   ag=frappe.db.get_value("Funding Agreement",row.funding_agreement,["project","donor","status"],as_dict=True)
   if not ag: frappe.throw(_("Funding Agreement {0} does not exist.").format(row.funding_agreement))
   if ag.project and ag.project!=parent.name: frappe.throw(_("Funding Agreement {0} belongs to another project.").format(row.funding_agreement))
   if ag.donor and ag.donor!=row.donor: frappe.throw(_("Funding Agreement donor must match the Project Funding Source donor."))

def validate_budget_line(doc,method=None):
 apply_budget_line_defaults(doc)
 if doc.get("is_group"): return
 if doc.get("eligibility_start_date") and doc.get("eligibility_end_date") and getdate(doc.eligibility_start_date)>getdate(doc.eligibility_end_date): frappe.throw(_("Eligibility Start Date cannot be after Eligibility End Date."))
 if not 0<=flt(doc.get("flexibility_percent"))<=100: frappe.throw(_("Flexibility must be between 0 and 100%."))
 if doc.get("funding_agreement"):
  agreement=frappe.db.get_value("Funding Agreement",doc.funding_agreement,["project","status"],as_dict=True)
  if not agreement: frappe.throw(_("Funding Agreement does not exist."))
  if agreement.project and agreement.project!=doc.project: frappe.throw(_("Budget Line project must match the Funding Agreement project."))
  if agreement.status in ("Closed","Cancelled"): frappe.throw(_("Closed or cancelled Funding Agreements cannot be used."))

def validate_accounting_document(doc,method=None):
 cfg=settings()
 rows=[doc]+[r for f in doc.meta.fields if f.fieldtype=="Table" for r in (doc.get(f.fieldname) or [])]
 for row in rows:
  line=row.get("budget_line") if hasattr(row,"get") else None
  if not line: continue
  data=frappe.db.get_value("Budget Line",line,["project","status","funding_agreement","eligibility_start_date","eligibility_end_date"],as_dict=True)
  if not data: frappe.throw(_("Budget Line {0} does not exist.").format(line))
  project=row.get("project") or doc.get("project")
  if project and data.project!=project: frappe.throw(_("Budget Line {0} belongs to another project.").format(line))
  if data.status=="Inactive": frappe.throw(_("Inactive Budget Line {0} cannot be used.").format(line))
  if cfg["require_agreement"] and not data.funding_agreement: frappe.throw(_("Budget Line {0} requires a Funding Agreement.").format(line))
  date=doc.get("posting_date") or doc.get("transaction_date") or doc.get("schedule_date")
  if cfg["eligibility"] and date:
   if data.eligibility_start_date and getdate(date)<getdate(data.eligibility_start_date): frappe.throw(_("Transaction date is before the Budget Line eligibility period."))
   if data.eligibility_end_date and getdate(date)>getdate(data.eligibility_end_date): frappe.throw(_("Transaction date is after the Budget Line eligibility period."))

def apply_funding_agreement_to_source_row(row, agreement):
    """Copy authoritative agreement values to a Project Funding Source row."""
    mapping = {
        "donor": "donor",
        "agreement_reference": "agreement_reference",
        "agreement_currency": "donor_currency",
        "agreement_amount": "approved_amount_donor_currency",
        "exchange_rate": "exchange_rate",
        "start_date": "funding_start_date",
        "end_date": "funding_end_date",
        "eligibility_start_date": "eligibility_start_date",
        "eligibility_end_date": "eligibility_end_date",
        "flexibility_percent": "flexibility_percent",
    }
    for source, target in mapping.items():
        if row.meta.has_field(target):
            row.set(target, agreement.get(source))


def validate_project_funding_source(doc, method=None):
    """Validate and hydrate funding rows from their selected agreements."""
    for row in doc.get("custom_funding_sources") or []:
        if not row.get("funding_agreement"):
            continue
        agreement = frappe.get_doc("Funding Agreement", row.funding_agreement)
        if agreement.project != doc.name:
            frappe.throw(_("Funding Agreement {0} does not belong to Project {1}.").format(agreement.name, doc.name))
        if row.donor and row.donor != agreement.donor:
            frappe.throw(_("Funding Agreement {0} belongs to donor {1}, not {2}.").format(agreement.name, agreement.donor, row.donor))
        apply_funding_agreement_to_source_row(row, agreement)
