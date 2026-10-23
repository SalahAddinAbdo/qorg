(() => {
    const protectedPolicies = new Set(["Read Only", "Feature Disabled", "Deprecated", "Restricted"]);

    async function getPolicy(doctype) {
        if (!doctype || frappe.session.user === "Administrator") return "Enabled";
        try {
            const result = await frappe.call({
                method: "qorg.qorg.enterprise_foundation.api.get_model_policy",
                args: { document_type: doctype },
                silent: true,
            });
            return result.message?.policy || "Enabled";
        } catch (error) {
            return "Enabled";
        }
    }

    async function applyPolicy() {
        const route = frappe.get_route();
        const doctype = window.cur_frm?.doctype || window.cur_list?.doctype || route?.[1];
        const policy = await getPolicy(doctype);
        if (!protectedPolicies.has(policy)) return;

        if (window.cur_frm?.doctype === doctype) {
            cur_frm.disable_save();
            cur_frm.set_read_only();
            cur_frm.page.clear_primary_action();
            cur_frm.page.set_indicator(__(policy), policy === "Restricted" ? "red" : "orange");
        }
        if (window.cur_list?.doctype === doctype) {
            cur_list.page.clear_primary_action();
            cur_list.page.set_indicator(__(policy), policy === "Restricted" ? "red" : "orange");
        }
    }

    frappe.router.on("change", () => setTimeout(applyPolicy, 150));
})();
