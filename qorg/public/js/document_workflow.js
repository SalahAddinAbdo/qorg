// ============================================================
// Unified Workflow Handler for Frappe 16
// Uses the native Frappe Workflow actions menu and routes execution through Q Org.
// Change only the DocType name when copying this script.
// ============================================================
wf_install_standard_workflow_actions();

window.qorg_initialize_document_workflow = function (frm) {
    wf_install_standard_workflow_actions();
    frm = frm || window.cur_frm;
    if (!frm || frm.__qorg_workflow_handler_registered) return;
    frm.__qorg_workflow_handler_registered = true;

    frappe.ui.form.on(frm.doctype, {
        setup(current) {
            wf_restrict_employee_signatures(current);
        },
        onload(current) {
            wf_prepare_new_document(current);
        },
        refresh(current) {
            wf_restrict_employee_signatures(current);
            wf_protect_document(current);
        }
    });

    wf_restrict_employee_signatures(frm);
    wf_prepare_new_document(frm);
    if (!frm.is_new()) wf_protect_document(frm);
};

window.qorg_initialize_document_workflow(window.cur_frm);

// Clear responsibility copied from a source document. The server repeats this
// protection for imports and API-created documents.
function wf_prepare_new_document(frm) {
    if (!frm.is_new() || frm.__wf_new_document_prepared) return;
    const workflow = frappe.workflow?.workflows?.[frm.doctype];
    const fields = new Set(["custom_current_responsible_user", "custom_previous_responsible_user"]);
    fields.forEach(fieldname => {
        if (frm.fields_dict?.[fieldname] && frm.doc[fieldname]) {
            frappe.model.set_value(frm.doc.doctype, frm.doc.name, fieldname, "");
        }
    });
    frm.__wf_new_document_prepared = true;
}

// Restrict every visible/editable Employee Signature link to the session user.
function wf_restrict_employee_signatures(frm) {
    if (frappe.session.user === "Administrator") return;

    (frm.meta?.fields || [])
        .filter(df =>
            df.fieldname &&
            df.fieldtype === "Link" &&
            df.options === "Employee Signature"
        )
        .forEach(df => {
            frm.set_query(df.fieldname, () => ({
                filters: { user_id: frappe.session.user }
            }));
        });
}

function wf_install_standard_workflow_actions() {
    const States = frappe?.ui?.form?.States;
    const prototype = States?.prototype;
    if (!prototype?.show_actions || prototype.__qorg_standard_actions_installed) return false;

    const original_show_actions = prototype.show_actions;
    Object.defineProperty(prototype, "__qorg_standard_actions_installed", {
        value: true,
        configurable: false,
        enumerable: false,
        writable: false
    });

    prototype.show_actions = function (...args) {
        const frm = this.frm;
        const workflow = frm && frappe.workflow?.workflows?.[frm.doctype];
        if (!wf_is_qorg_workflow(workflow)) {
            return original_show_actions.apply(this, args);
        }
        return wf_show_standard_actions(this, workflow);
    };
    return true;
}

function wf_is_qorg_workflow(workflow) {
    return Boolean(
        workflow?.transitions?.some((row) =>
            Object.prototype.hasOwnProperty.call(row, "custom_responsibility_routing")
        )
    );
}

async function wf_show_standard_actions(states, workflow) {
    const frm = states?.frm;
    if (!frm || frm.is_new()) return;

    const request_id = (states.__qorg_actions_request_id || 0) + 1;
    states.__qorg_actions_request_id = request_id;
    frm.page?.clear_actions_menu?.();
    if (frm.is_dirty()) return;

    let allowed;
    try {
        allowed = await frappe.xcall("frappe.model.workflow.get_transitions", {doc: frm.doc});
    } catch (error) {
        console.error("Unable to load workflow transitions", error);
        frappe.show_alert({
            message: __("Workflow actions could not be loaded. Please refresh the page."),
            indicator: "orange"
        });
        return;
    }

    if (
        window.cur_frm !== frm ||
        frm.is_dirty() ||
        states.__qorg_actions_request_id !== request_id
    ) return;
    const configured = workflow.transitions || [];
    const state_field = workflow.workflow_state_field || workflow.state_fieldname || "workflow_state";
    const current_state = wf_normalize(frm.doc[state_field]);
    const can_execute = wf_can_execute_workflow(frm);

    (allowed || []).forEach((allowed_transition) => {
        const action = String(allowed_transition.action || "").trim();
        if (!action) return;
        const transition = configured.find((row) =>
            wf_normalize(row.action) === wf_normalize(action) &&
            wf_normalize(row.state) === current_state
        );
        if (!transition || !can_execute) return;

        frm.page.add_action_item(__(action), () =>
            wf_run_standard_action(frm, workflow, transition)
        );
    });
}

async function wf_run_standard_action(frm, workflow, transition) {
    if (frm.__wf_processing) {
        frappe.show_alert({
            message: __("A workflow action is already being processed. Please wait."),
            indicator: "orange"
        });
        return;
    }
    if (frm.is_dirty()) {
        wf_message(
            __("Unsaved Changes"),
            __("The document contains unsaved changes. Please save it before continuing.")
        );
        return;
    }

    const proceed = async () => {
        try {
            await wf_open_action_dialog(frm, transition);
        } catch (error) {
            console.error("Workflow action dialog failed", error);
            wf_show_error(error);
        }
    };

    if (workflow?.enable_action_confirmation) {
        frappe.confirm(
            __("Are you sure you want to perform the workflow action {0}?", [__(transition.action || "")]),
            proceed
        );
        return;
    }
    await proceed();
}

function wf_can_execute_workflow(frm) {
    const responsible = String(frm.doc.custom_current_responsible_user || "").trim();
    const current = String(frappe.session.user || "").trim();
    if (!responsible || responsible === current) return true;
    const roles = new Set(frappe.user_roles || []);
    return current === "Administrator" || roles.has("System Manager") || roles.has("Workflow Admin");
}

async function wf_open_action_dialog(frm, transition) {
    if (frm.__wf_processing) {
        frappe.show_alert({
            message: __("A workflow action is already being processed. Please wait."),
            indicator: "orange"
        });
        return;
    }

    const routing = String(transition.custom_responsibility_routing || "Keep Current Responsible").trim();
    const assignment_required = routing === "Select Next User";
    const apply_signature = wf_checked(transition.custom_apply_employee_signature);
    const target_role = String(transition.custom_target_role || "").trim();
    const show_user = assignment_required;
    const signature_context = apply_signature
        ? await wf_get_signature_dialog_context(frm, transition)
        : { include_signature_notes: false, signature_notes: "" };


    const fields = [];
    const automatic_user = routing === "Return to Previous Responsible"
        ? String(frm.doc.custom_previous_responsible_user || "").trim()
        : routing === "Return to Document Creator"
            ? String(frm.doc.owner || "").trim()
            : "";

    if (["Return to Previous Responsible", "Return to Document Creator"].includes(routing)) {
        fields.push({
            fieldname: "resolved_user",
            label: __("Next Responsible User"),
            fieldtype: "Link",
            options: "User",
            default: automatic_user,
            read_only: 1,
            description: routing === "Return to Previous Responsible"
                ? __("Resolved automatically from the user who sent the previous handoff.")
                : __("Resolved automatically from the document owner.")
        });
    }

    if (show_user) {
        fields.push({
            fieldname: "user",
            label: __("Next Responsible User"),
            fieldtype: "Link",
            options: "User",
            reqd: 1,
            description: target_role
                ? __(
                    "Select an enabled user with role {0}. You may select yourself if you hold this role.",
                    [__(target_role)]
                )
                : __(
                    "Select the user responsible for the next stage. You may select yourself when appropriate."
                ),
            get_query() {
                const filters = { enabled: 1 };
                if (target_role) filters.role = target_role;
                return {
                    query: "frappe.core.doctype.user.user.user_query",
                    filters
                };
            }
        });
    }

    if (apply_signature && signature_context.include_signature_notes) {
        fields.push({
            fieldname: "signature_notes",
            label: __("Signature Notes"),
            fieldtype: "Small Text",
            reqd: 0,
            default: signature_context.signature_notes || "",
            description: __("Optional. The previously saved note is shown here and may be retained or updated.")
        });
    }

    fields.push({
        fieldname: "workflow_comment",
        label: __("Internal Comment"),
        fieldtype: "Small Text",
        reqd: 0,
        description: __("Optional. The comment will be recorded after the workflow action succeeds.")
    });

    const dialog = new frappe.ui.Dialog({
        title: __(transition.custom_workflow_prompt || transition.action || "Workflow Action"),
        fields,
        primary_action_label: show_user ? __("Assign & Continue") : __("Continue"),
        primary_action: async values => {
            const selected_user = String(values?.user || "").trim();
            const signature_notes = String(values?.signature_notes || "").trim();
            const comment = String(values?.workflow_comment || "").trim();

            if (assignment_required && !selected_user) {
                frappe.show_alert({
                    message: __("Please select the next responsible user."),
                    indicator: "orange"
                });
                return;
            }

            dialog.disable_primary_action();
            const completed = await wf_run_transition(
                frm,
                transition,
                selected_user,
                signature_notes,
                comment
            );
            dialog.hide();

            if (!completed) {
                try {
                    await frm.reload_doc();
                } catch (reload_error) {
                    console.error(
                        "Unable to reload document after workflow failure",
                        reload_error
                    );
                }
            }
        }
    });

    dialog.show();
    setTimeout(() => {
        dialog.fields_dict?.[
            show_user
                ? "user"
                : (apply_signature && signature_context.include_signature_notes
                    ? "signature_notes"
                    : "workflow_comment")
        ]?.set_focus?.();
    }, 150);
}

async function wf_get_signature_dialog_context(frm, transition) {
    const mapping_key = String(
        transition.custom_employee_signature_mapping_key || ""
    ).trim();
    if (!mapping_key || frm.is_new() || !frm.doc.name) {
        return { include_signature_notes: false, signature_notes: "" };
    }
    try {
        const result = await frappe.xcall(
            "qorg.qorg.api.signatures.get_signature_dialog_context",
            {
                doctype: frm.doc.doctype,
                document_name: frm.doc.name,
                mapping_key
            }
        );
        return {
            include_signature_notes: wf_checked(result?.include_signature_notes),
            signature_notes: String(result?.signature_notes || "")
        };
    } catch (error) {
        console.error("Unable to load signature dialog context", error);
        wf_show_error(error);
        return { include_signature_notes: false, signature_notes: "" };
    }
}

async function wf_run_transition(frm, transition, selected_user = "", signature_notes = "", comment = "") {
    if (frm.__wf_processing) return false;

    if (frm.is_dirty()) {
        wf_message(
            __("Unsaved Changes"),
            __("The document contains unsaved changes. Please save it before continuing.")
        );
        return false;
    }

    frm.__wf_processing = true;
    frm.selected_workflow_action = String(transition.action || "").trim();
    let frozen = false;

    try {
        await frm.script_manager.trigger("before_workflow_action");
        frappe.dom.freeze(__("Processing workflow action..."));
        frozen = true;

        const result = await frappe.xcall(
            "qorg.qorg.workflow.actions.apply_assigned_workflow_action",
            {
                doctype: frm.doc.doctype,
                document_name: frm.doc.name,
                action: String(transition.action || "").trim(),
                next_user: String(selected_user || "").trim(),
                signature_notes: String(signature_notes || "").trim(),
                internal_comment: String(comment || "").trim(),
                expected_modified: frm.doc.modified || ""
            }
        );

        if (!result?.doc) {
            frappe.throw(__("The workflow service returned no updated document."));
        }

        frappe.model.sync(result.doc);
        await frm.reload_doc();
        await frm.script_manager.trigger("after_workflow_action");

        frappe.show_alert({
            message: result.comment_recorded
                ? __("Workflow action {0} completed and the comment was recorded.", [transition.action || ""])
                : __("Workflow action {0} completed successfully.", [transition.action || ""]),
            indicator: "green"
        });
        return true;
    } catch (error) {
        console.error("Workflow action failed", error);
        wf_show_error(error);
        return false;
    } finally {
        if (frozen) frappe.dom.unfreeze();
        frm.selected_workflow_action = null;
        frm.__wf_processing = false;
    }
}

function wf_protect_document(frm) {
    const responsible = String(
        frm.doc.custom_current_responsible_user || ""
    ).trim();
    if (!responsible) {
        wf_unlock_document_fields(frm);
        return true;
    }
    const can_override =
        frappe.session.user === "Administrator" ||
        frappe.user.has_role("Workflow Admin") ||
        frappe.user.has_role("System Manager");
    const is_responsible =
        wf_normalize(frappe.session.user) === wf_normalize(responsible);
    if (is_responsible || can_override) {
        wf_unlock_document_fields(frm);
        return true;
    }

    // Lock document data only. Do not call disable_form(), clear_menu(), or
    // clear_actions_menu(), because ERPNext places permitted related-document
    // actions such as Request for Quotation and Purchase Order in those menus.
    wf_lock_document_fields(frm);
    wf_hide_workflow_actions_only(frm);

    if (!frm.__wf_responsibility_alert_shown) {
        frm.__wf_responsibility_alert_shown = true;
        frappe.show_alert({
            message: __("This document is assigned to {0}. You may read it and use permitted standard actions, but only the responsible user can edit it or perform workflow actions.", [responsible]),
            indicator: "orange"
        });
    }
    return false;
}

function wf_lock_document_fields(frm) {
    if (frm.__wf_fields_locked) return;
    frm.__wf_original_field_state = {};
    (frm.meta?.fields || []).forEach(df => {
        const control = frm.fields_dict?.[df.fieldname];
        if (!df.fieldname || !control || [
            "Section Break", "Column Break", "Tab Break", "HTML",
            "Button", "Heading", "Fold"
        ].includes(df.fieldtype)) return;
        frm.__wf_original_field_state[df.fieldname] = {
            read_only: Boolean(df.read_only),
            cannot_add_rows: control.grid?.cannot_add_rows ?? null,
            cannot_delete_rows: control.grid?.cannot_delete_rows ?? null
        };
        frm.set_df_property(df.fieldname, "read_only", 1);
        if (control.grid) {
            control.grid.cannot_add_rows = true;
            control.grid.cannot_delete_rows = true;
            control.grid.wrapper
                .find(".grid-add-row,.grid-remove-rows,.grid-delete-row")
                .hide();
        }
    });
    frm.__wf_fields_locked = true;
    frm.refresh_fields();
}

function wf_unlock_document_fields(frm) {
    if (!frm.__wf_fields_locked) return;
    Object.entries(frm.__wf_original_field_state || {}).forEach(([fieldname, state]) => {
        const control = frm.fields_dict?.[fieldname];
        if (!control) return;
        frm.set_df_property(fieldname, "read_only", state.read_only ? 1 : 0);
        if (control.grid) {
            if (state.cannot_add_rows !== null) {
                control.grid.cannot_add_rows = state.cannot_add_rows;
            }
            if (state.cannot_delete_rows !== null) {
                control.grid.cannot_delete_rows = state.cannot_delete_rows;
            }
            if (!state.cannot_add_rows) control.grid.wrapper.find(".grid-add-row").show();
            if (!state.cannot_delete_rows) {
                control.grid.wrapper.find(".grid-remove-rows,.grid-delete-row").show();
            }
        }
    });
    frm.__wf_fields_locked = false;
    frm.refresh_fields();
}

function wf_show_error(error) {
    let message = "";
    try {
        message = JSON.parse(error?._server_messages || "[]")
            .map(item => {
                try { return JSON.parse(item).message; }
                catch { return item; }
            })
            .filter(Boolean)
            .join("<br>");
    } catch {
        message = "";
    }

    frappe.msgprint({
        title: __("Workflow Action Failed"),
        message: message || error?.message || __("The workflow action could not be completed. Please review the document and try again."),
        indicator: "red"
    });
}

function wf_message(title, message) {
    frappe.msgprint({ title, message, indicator: "red" });
}

function wf_checked(value) {
    return value === true || value === 1 || String(value || "") === "1";
}

function wf_normalize(value) {
    return String(value ?? "")
        .replace(/\u00A0/g, " ")
        .replace(/[\u200B-\u200F\u202A-\u202E\u2060\uFEFF]/g, "")
        .replace(/\s+/g, " ")
        .trim()
        .toLowerCase();
}

