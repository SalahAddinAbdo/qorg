(() => {
    if (window.__qorg_model_policy_loaded) return;
    window.__qorg_model_policy_loaded = true;
    let action_policies = { ...(frappe.boot.qorg_action_policies || {}) };

    async function reload_policies() {
        const response = await frappe.call({method:"qorg.qorg.enterprise_foundation.api.get_action_policies", silent:true});
        action_policies = response.message || {};
        frappe.boot.qorg_action_policies = action_policies;
    }

    function hide_add_controls(frm, config) {
        const wrapper = $(frm.page?.wrapper || frm.wrapper);
        if (!config.allow_comments) wrapper.find(".comment-box").hide();
        else wrapper.find(".comment-box").show();
        const attachment_add = wrapper.find(".add-attachment, .attachment-btn, [data-label='Add Attachment']");
        if (!config.allow_attachments) attachment_add.hide(); else attachment_add.show();
    }

    window.qorg_apply_model_policy = async function(frm) {
        frm = frm || window.cur_frm;
        if (!frm?.doctype || frappe.session.user === "Administrator") return;
        if (!Object.prototype.hasOwnProperty.call(action_policies, frm.doctype)) await reload_policies();
        const config = action_policies[frm.doctype];
        if (!config || config.policy !== "View Only") return;
        // Native Custom DocPerm protects data. This runs after all Q Org workflow
        // and dimension controllers, and only removes form action surfaces.
        frm.clear_custom_buttons?.();
        frm.page?.clear_primary_action?.();
        frm.page?.clear_secondary_action?.();
        frm.page?.clear_actions_menu?.();
        frm.page?.clear_inner_toolbar?.();
        if (!config.allow_print) frm.page?.menu?.find("[data-label='Print'], [data-label='Print View']").closest("li").hide();
        if (!config.allow_email) frm.page?.menu?.find("[data-label='Email'], [data-label='New Email']").closest("li").hide();
        hide_add_controls(frm, config);
        frm.__qorg_model_policy_applied = true;
    };

    frappe.realtime.on("qorg_model_policy_changed", async () => {
        await reload_policies();
        if (window.cur_frm) window.qorg_apply_model_policy(window.cur_frm);
    });
})();
