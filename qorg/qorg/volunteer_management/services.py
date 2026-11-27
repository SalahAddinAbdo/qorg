from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import add_days, cint, flt, getdate, now_datetime


EXCLUDED_SERVICE_LOG_STATUSES = ("Rejected", "Cancelled")


def settings():
    hr = frappe.get_single("HR Settings")
    maximum_hours_per_day = flt(hr.get("qorg_participation_max_daily_hours"))
    maximum_hours_per_week = flt(hr.get("qorg_participation_max_weekly_hours"))

    values = {
        "default_participation_type": hr.get("qorg_participation_default_type"),
        "default_minimum_age": cint(hr.get("qorg_participation_minimum_age")),
        "require_agreement": cint(hr.get("qorg_participation_require_agreement")),
        "require_code_of_conduct": cint(hr.get("qorg_participation_require_code")),
        "require_safeguarding_acknowledgement": cint(
            hr.get("qorg_participation_require_safeguarding")
        ),
        "require_learning_objectives": cint(
            hr.get("qorg_participation_require_learning_objectives")
        ),
        "require_midterm_evaluation": cint(
            hr.get("qorg_participation_require_midterm")
        ),
        "require_decision_rationale": cint(
            hr.get("qorg_participation_require_decision_rationale")
        ),
        "maximum_hours_per_day": maximum_hours_per_day,
        "maximum_hours_per_week": maximum_hours_per_week,
        "require_service_log_evidence": cint(
            hr.get("qorg_participation_require_evidence")
        ),
        "require_supervisor_verification": cint(
            hr.get("qorg_participation_require_supervisor_verification")
        ),
        "allow_overachievement": cint(
            hr.get("qorg_participation_allow_overachievement")
        ),
        "prevent_start_with_pending_clearance": cint(
            hr.get("qorg_participation_block_pending_clearance")
        ),
        "require_final_evaluation": cint(
            hr.get("qorg_participation_require_final")
        ),
    }
    return frappe._dict(values)


def validate_weighted_rows(rows, label):
    if not rows:
        return

    total = sum(flt(row.weight) for row in rows)
    if abs(total - 100) > 0.01:
        difference = 100 - total
        frappe.throw(
            _(
                "{0} weights must total 100%. Current total: {1}%. "
                "Required adjustment: {2}{3}%."
            ).format(
                label,
                total,
                "add " if difference > 0 else "remove ",
                abs(difference),
            )
        )


def validate_opportunity(doc, method=None):
    participation_settings = settings()
    if not doc.get("qorg_participation_type"):
        doc.qorg_participation_type = participation_settings.default_participation_type
    if not doc.get("qorg_participation_type"):
        return
    if not cint(doc.get("qorg_minimum_age")):
        doc.qorg_minimum_age = participation_settings.default_minimum_age

    if cint(doc.get("qorg_number_of_positions")) < 1:
        frappe.throw(_("Number of Positions must be at least 1."))

    screening_weight = flt(doc.get("qorg_screening_weight"))
    assessment_weight = flt(doc.get("qorg_assessment_weight"))
    if abs(screening_weight + assessment_weight - 100) > 0.01:
        frappe.throw(
            _(
                "Screening and Assessment weights must total exactly 100%. "
                "Current total: {0}%."
            ).format(screening_weight + assessment_weight)
        )

    validate_weighted_rows(
        doc.get("qorg_assessment_plan") or [],
        _("Assessment stage"),
    )


def validate_application(doc, method=None):
    prevent_duplicate_application(doc)
    validate_unique_priority(doc)
    validate_screening(doc)

    if (
        doc.available_from
        and doc.available_to
        and getdate(doc.available_to) < getdate(doc.available_from)
    ):
        frappe.throw(_("Available To cannot be before Available From."))

    if (
        doc.final_decision
        and settings().require_decision_rationale
        and not (doc.decision_rationale or "").strip()
    ):
        frappe.throw(_("Decision Rationale is required."))

    if doc.final_decision and not doc.decision_on:
        doc.decision_on = now_datetime()
        doc.decision_by = frappe.session.user


def load_assessment_stage(doc):
    if not doc.application:
        return

    application = frappe.get_doc("Participation Application", doc.application)
    doc.opportunity = application.opportunity

    stage = frappe.db.get_value(
        "Participation Assessment Stage",
        {
            "parent": application.opportunity,
            "parenttype": "External Opportunity",
            "parentfield": "qorg_assessment_plan",
            "sequence": doc.stage_sequence,
        },
        [
            "stage_name",
            "assessment_method",
            "passing_score",
            "allow_retry",
            "maximum_attempts",
            "retry_requires_approval",
        ],
        as_dict=True,
    )
    if not stage:
        frappe.throw(
            _("Assessment stage {0} is not configured for the linked opportunity.").format(
                doc.stage_sequence
            )
        )

    for field in stage:
        if doc.meta.has_field(field) and not doc.get(field):
            doc.set(field, stage[field])


def validate_assessment(doc, method=None):
    load_assessment_stage(doc)

    if doc.status == "Completed":
        if doc.score is None:
            frappe.throw(_("Score is required for a completed assessment."))

        passing_score = frappe.db.get_value(
            "Participation Assessment Stage",
            {
                "parent": doc.opportunity,
                "parenttype": "External Opportunity",
                "parentfield": "qorg_assessment_plan",
                "sequence": doc.stage_sequence,
            },
            "passing_score",
        )
        if passing_score is None:
            frappe.throw(
                _("Set the Passing Score for assessment stage {0} in the linked opportunity.").format(
                    doc.stage_sequence
                )
            )
        doc.result = "Passed" if flt(doc.score) >= flt(passing_score) else "Failed"


def recalculate_application(application):
    if not application or not frappe.db.exists("Participation Application", application):
        return

    app = frappe.get_doc("Participation Application", application)
    opportunity = frappe.get_doc("External Opportunity", app.opportunity)
    stages = opportunity.get("qorg_assessment_plan") or []

    weighted_score = 0
    completed_weight = 0
    for stage in stages:
        current = frappe.get_all(
            "Participation Assessment",
            filters={
                "application": app.name,
                "stage_sequence": stage.sequence,
                "status": "Completed",
            },
            fields=["score", "attempt_number"],
            order_by="attempt_number desc, modified desc",
            limit_page_length=1,
        )
        if not current:
            continue

        weighted_score += flt(current[0].score) * flt(stage.weight)
        completed_weight += flt(stage.weight)

    assessment_score = (
        flt(weighted_score / completed_weight, 2) if completed_weight else 0
    )
    overall_score = flt(
        flt(app.screening_score) * flt(opportunity.qorg_screening_weight) / 100
        + assessment_score * flt(opportunity.qorg_assessment_weight) / 100,
        2,
    )

    frappe.db.set_value(
        "Participation Application",
        app.name,
        {
            "assessment_score": assessment_score,
            "overall_score": overall_score,
        },
        update_modified=False,
    )
    rank_applications(app.opportunity)


def rank_applications(opportunity):
    rows = frappe.get_all(
        "Participation Application",
        filters={"opportunity": opportunity, "status": ["not in", ["Withdrawn", "Cancelled"]]},
        fields=["name"],
        order_by="overall_score desc, creation asc",
    )
    for index, row in enumerate(rows, 1):
        frappe.db.set_value(
            "Participation Application",
            row.name,
            "ranking",
            index,
            update_modified=False,
        )


def validate_engagement(doc, method=None):
    if doc.start_date and doc.end_date and getdate(doc.end_date) < getdate(doc.start_date):
        frappe.throw(_("End Date cannot be before Start Date."))

    participation_settings = settings()
    if doc.status == "Active":
        if participation_settings.prevent_start_with_pending_clearance and (
            doc.safeguarding_clearance_status == "Pending"
            or doc.background_check_status == "Pending"
        ):
            frappe.throw(_("Required clearances must be completed before activation."))
        if participation_settings.require_agreement and doc.agreement_status != "Accepted":
            frappe.throw(_("The participation agreement must be accepted before activation."))
        if participation_settings.require_code_of_conduct and not cint(
            doc.code_of_conduct_accepted
        ):
            frappe.throw(_("Code of Conduct acceptance is required before activation."))
        if participation_settings.require_safeguarding_acknowledgement and not cint(
            doc.safeguarding_acknowledged
        ):
            frappe.throw(_("Safeguarding acknowledgement is required before activation."))
        if (
            doc.participation_type == "Intern"
            and participation_settings.require_learning_objectives
            and not (doc.get("learning_objectives") or [])
        ):
            frappe.throw(_("Learning Objectives are required before activating an internship."))

    rows = doc.get("onboarding_activities") or []
    doc.onboarding_completion = (
        flt(
            sum(1 for row in rows if row.status in ("Completed", "Waived"))
            * 100
            / len(rows),
            2,
        )
        if rows
        else 0
    )

    if doc.status == "Completed":
        if (
            participation_settings.require_midterm_evaluation
            and not doc.latest_midterm_evaluation
        ):
            frappe.throw(_("A completed Midterm Evaluation is required before completion."))
        if (
            participation_settings.require_final_evaluation
            and not doc.latest_final_evaluation
        ):
            frappe.throw(_("A completed Final Evaluation is required before completion."))
        if participation_settings.require_final_evaluation and not doc.final_rating:
            frappe.throw(_("Final Rating is required before completion."))


def validate_weekly_service_hours(doc, maximum_hours_per_week):
    if not doc.engagement or not doc.service_date:
        return

    service_date = getdate(doc.service_date)
    week_start = add_days(service_date, -service_date.weekday())
    week_end = add_days(week_start, 6)

    existing_hours = frappe.db.sql(
        """
        SELECT COALESCE(SUM(hours), 0)
        FROM `tabParticipation Service Log`
        WHERE engagement = %(engagement)s
          AND name != %(name)s
          AND service_date BETWEEN %(week_start)s AND %(week_end)s
          AND status NOT IN %(excluded_statuses)s
        """,
        {
            "engagement": doc.engagement,
            "name": doc.name or "",
            "week_start": week_start,
            "week_end": week_end,
            "excluded_statuses": EXCLUDED_SERVICE_LOG_STATUSES,
        },
    )[0][0]

    total_hours = flt(existing_hours) + flt(doc.hours)
    if total_hours > flt(maximum_hours_per_week):
        frappe.throw(
            _(
                "Weekly service hours cannot exceed {0}. Existing hours for this week: {1}. "
                "Current entry: {2}. Resulting total: {3}."
            ).format(
                flt(maximum_hours_per_week),
                flt(existing_hours),
                flt(doc.hours),
                total_hours,
            )
        )


def validate_service_log_verifier(doc, participation_settings):
    if doc.status != "Verified" or not participation_settings.require_supervisor_verification:
        return
    if frappe.session.user == "Administrator":
        return

    supervisor_user = frappe.db.get_value("Employee", doc.supervisor, "user_id")
    if not supervisor_user or supervisor_user != frappe.session.user:
        frappe.throw(_("Only the engagement supervisor can verify this service log."))


def validate_expected_hours(doc, participation_settings):
    if participation_settings.allow_overachievement or not doc.engagement:
        return

    expected_hours = flt(
        frappe.db.get_value(
            "Participation Engagement",
            doc.engagement,
            "expected_hours",
        )
    )
    if expected_hours <= 0:
        return

    existing_hours = frappe.db.sql(
        """
        SELECT COALESCE(SUM(hours), 0)
        FROM `tabParticipation Service Log`
        WHERE engagement = %(engagement)s
          AND name != %(name)s
          AND status NOT IN %(excluded_statuses)s
        """,
        {
            "engagement": doc.engagement,
            "name": doc.name or "",
            "excluded_statuses": EXCLUDED_SERVICE_LOG_STATUSES,
        },
    )[0][0]
    resulting_total = flt(existing_hours) + flt(doc.hours)
    if resulting_total > expected_hours:
        frappe.throw(
            _(
                "Service hours cannot exceed the engagement expected total of {0}. "
                "Resulting total: {1}."
            ).format(expected_hours, resulting_total)
        )


def validate_service_log(doc, method=None):
    participation_settings = settings()

    if doc.engagement:
        engagement = frappe.db.get_value(
            "Participation Engagement",
            doc.engagement,
            ["external_person", "supervisor"],
            as_dict=True,
        )
        if engagement:
            doc.external_person = engagement.external_person
            doc.supervisor = engagement.supervisor

    if participation_settings.maximum_hours_per_day <= 0:
        frappe.throw(
            _("Set Maximum Hours per Day in HR Settings before using participation service logs.")
        )
    if participation_settings.maximum_hours_per_week <= 0:
        frappe.throw(
            _("Set Maximum Hours per Week in HR Settings before using participation service logs.")
        )
    if (
        participation_settings.maximum_hours_per_week
        < participation_settings.maximum_hours_per_day
    ):
        frappe.throw(
            _("Maximum Hours per Week cannot be less than Maximum Hours per Day in HR Settings.")
        )

    if flt(doc.hours) <= 0:
        frappe.throw(_("Hours must be greater than zero."))
    if flt(doc.hours) > flt(participation_settings.maximum_hours_per_day):
        frappe.throw(_("Hours exceed the maximum allowed per day."))

    validate_weekly_service_hours(
        doc,
        participation_settings.maximum_hours_per_week,
    )
    validate_expected_hours(doc, participation_settings)
    validate_service_log_verifier(doc, participation_settings)

    if participation_settings.require_service_log_evidence and not doc.evidence:
        frappe.throw(_("Evidence is required."))
    if doc.status == "Rejected" and not (doc.rejection_reason or "").strip():
        frappe.throw(_("Rejection Reason is required."))


def update_verified_hours(engagement):
    if not engagement or not frappe.db.exists("Participation Engagement", engagement):
        return

    total = frappe.db.sql(
        """
        SELECT COALESCE(SUM(hours), 0)
        FROM `tabParticipation Service Log`
        WHERE engagement = %s AND status = 'Verified'
        """,
        engagement,
    )[0][0]
    frappe.db.set_value(
        "Participation Engagement",
        engagement,
        "completed_hours",
        total,
        update_modified=False,
    )


def prevent_duplicate_application(doc):
    active_statuses = [
        "Draft",
        "Under Screening",
        "Screened In",
        "Under Assessment",
        "Selected",
        "Reserve / Waitlisted",
    ]
    duplicate = frappe.db.get_value(
        "Participation Application",
        {
            "external_person": doc.external_person,
            "opportunity": doc.opportunity,
            "status": ["in", active_statuses],
            "name": ["!=", doc.name or ""],
        },
        "name",
    )
    if duplicate:
        frappe.throw(_("An active application already exists: {0}").format(duplicate))


def validate_unique_priority(doc):
    if doc.final_decision in ("Selected", "Reserve / Waitlisted") and cint(
        doc.selection_priority
    ) <= 0:
        frappe.throw(_("Selection Priority is required."))

    if cint(doc.selection_priority) <= 0:
        return

    duplicate = frappe.db.get_value(
        "Participation Application",
        {
            "opportunity": doc.opportunity,
            "selection_priority": doc.selection_priority,
            "final_decision": ["in", ["Selected", "Reserve / Waitlisted"]],
            "name": ["!=", doc.name or ""],
        },
        "name",
    )
    if duplicate:
        frappe.throw(_("Selection Priority is already used by {0}.").format(duplicate))


def validate_screening(doc):
    rows = doc.get("screening_criteria") or []
    weighted_score = 0
    assessed_weight = 0

    for row in rows:
        if row.mandatory and row.result == "Not Met":
            doc.screening_score = 0
            return

        if row.result in ("Met", "Not Met"):
            value = 100 if row.result == "Met" else 0
            weighted_score += value * flt(row.weight)
            assessed_weight += flt(row.weight)
        elif row.score is not None:
            weighted_score += flt(row.score) * flt(row.weight)
            assessed_weight += flt(row.weight)

    doc.screening_score = (
        flt(weighted_score / assessed_weight, 2) if assessed_weight else 0
    )
