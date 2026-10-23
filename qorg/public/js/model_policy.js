(() => {
    if (frappe.session.user === "Administrator") return;

    let policies = { ...(frappe.boot.qorg_action_policies || {}) };
    let observer = null;
    let applying = false;
    let utilityRestore = false;

    const scrub = (value) => (value || "")
        .toString()
        .toLowerCase()
        .replace(/[_\s]+/g, "-")
        .replace(/[^a-z0-9-]/g, "")
        .replace(/-+/g, "-")
        .replace(/^-|-$/g, "");

    function routeDoctype() {
        const route = frappe.get_route() || [];
        const routeParts = route.map(scrub);
        return Object.keys(policies).find((doctype) => routeParts.includes(scrub(doctype))) || null;
    }

    function currentDoctype() {
        if (window.cur_frm?.doctype && policies[window.cur_frm.doctype]) return window.cur_frm.doctype;
        if (window.cur_list?.doctype && policies[window.cur_list.doctype]) return window.cur_list.doctype;
        return routeDoctype();
    }

    function currentConfig() {
        return policies[currentDoctype()] || { policy: "Standard" };
    }

    function isViewOnly() {
        return currentConfig().policy === "View Only";
    }

    function blocksWriteActions() {
        return ["Disable Write Actions", "View Only"].includes(currentConfig().policy);
    }

    function hide(selector) {
        document.querySelectorAll(selector).forEach((element) => {
            element.classList.add("qorg-action-hidden");
            element.setAttribute("aria-hidden", "true");
            element.setAttribute("tabindex", "-1");
        });
    }

    function clearOld() {
        document.querySelectorAll(".qorg-action-hidden").forEach((element) => {
            element.classList.remove("qorg-action-hidden");
            element.removeAttribute("aria-hidden");
            element.removeAttribute("tabindex");
        });
    }

    function restoreUtilities(frm, config) {
        if (!frm || utilityRestore) return;
        utilityRestore = true;
        try {
            if (config.allow_print) {
                frm.page.add_menu_item(__("Print"), () => frm.print_doc(), true);
            }
            if (config.allow_email && typeof frm.email_doc === "function") {
                frm.page.add_menu_item(__("Email"), () => frm.email_doc(), true);
            }
        } finally {
            utilityRestore = false;
        }
    }

    function enforceForm(config) {
        const frm = window.cur_frm;
        if (!frm) return;

        frm.disable_save();
        frm.set_read_only();
        frm.clear_custom_buttons?.();
        frm.page.clear_primary_action?.();
        frm.page.clear_secondary_action?.();
        frm.page.clear_actions_menu?.();
        frm.page.clear_inner_toolbar?.();

        if (config.policy === "View Only") {
            frm.page.clear_menu?.();
            restoreUtilities(frm, config);
        }
    }

    function enforceListOrTree(config) {
        const page = window.cur_list?.page || window.cur_tree?.page;
        page?.clear_primary_action?.();
        page?.clear_secondary_action?.();
        page?.clear_actions_menu?.();
        if (config.policy === "View Only") {
            page?.clear_inner_toolbar?.();
            page?.clear_menu?.();
        }
    }

    function enforceDom(config) {
        hide(
            ".page-head .primary-action, .page-head .btn-primary, " +
            ".page-actions .btn-primary, .standard-actions .btn-primary, " +
            ".grid-add-row, .tree-toolbar .btn-primary, .tree-node-toolbar .btn-primary, " +
            ".tree-actions .btn-primary, .new-node, .add-child"
        );

        if (config.policy === "View Only") {
            hide(
                ".custom-actions, .inner-toolbar, .inner-group-button, " +
                ".actions-btn-group, .menu-btn-group, .page-actions .btn, " +
                ".standard-actions .btn, .workflow-button-group"
            );
        }
        if (!config.allow_comments) {
            hide(".comment-box, .new-comment, .comment-input, [data-fieldname='comments']");
        }
        if (!config.allow_attachments) {
            hide(".attachments, .attachment-row, .form-attachments, [data-label='Attachments']");
        }
    }

    function applyPolicy() {
        if (applying) return;
        applying = true;
        try {
            clearOld();
            const config = currentConfig();
            if (!blocksWriteActions()) return;
            enforceForm(config);
            enforceListOrTree(config);
            enforceDom(config);
        } finally {
            applying = false;
        }
    }

    function schedule() {
        applyPolicy();
        requestAnimationFrame(applyPolicy);
        [50, 150, 400, 800, 1500, 2500].forEach((delay) => setTimeout(applyPolicy, delay));
    }

    async function reloadPolicies() {
        const result = await frappe.call({
            method: "qorg.qorg.enterprise_foundation.api.get_action_policies",
            silent: true,
        });
        policies = result.message || {};
        frappe.boot.qorg_action_policies = policies;
        schedule();
    }

    // Prevent late form scripts from re-adding action surfaces after policy enforcement.
    const Page = frappe.ui?.Page;
    if (Page?.prototype && !Page.prototype.__qorg_policy_patched) {
        Page.prototype.__qorg_policy_patched = true;
        ["set_primary_action", "set_secondary_action", "add_inner_button", "add_action_item"].forEach((method) => {
            const original = Page.prototype[method];
            if (typeof original !== "function") return;
            Page.prototype[method] = function (...args) {
                if (!utilityRestore && blocksWriteActions()) return null;
                return original.apply(this, args);
            };
        });
        ["add_menu_item"].forEach((method) => {
            const original = Page.prototype[method];
            if (typeof original !== "function") return;
            Page.prototype[method] = function (...args) {
                if (!utilityRestore && isViewOnly()) return null;
                return original.apply(this, args);
            };
        });
    }

    frappe.realtime.on("qorg_model_policy_changed", reloadPolicies);
    frappe.router.on("change", () => reloadPolicies().catch(schedule));
    $(document).on("page-change form-refresh list-rendered", schedule);

    observer = new MutationObserver(() => applyPolicy());
    observer.observe(document.body, { childList: true, subtree: true });
    reloadPolicies().catch(schedule);
})();
