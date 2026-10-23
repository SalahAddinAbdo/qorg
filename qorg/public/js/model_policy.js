(() => {
    if (frappe.session.user === "Administrator") return;

    let policies = { ...(frappe.boot.qorg_action_policies || {}) };
    let observer = null;
    let scheduled = null;

    const scrub = (value) => (value || "")
        .toString()
        .toLowerCase()
        .replace(/[_\s]+/g, "-")
        .replace(/[^a-z0-9-]/g, "")
        .replace(/-+/g, "-")
        .replace(/^-|-$/g, "");

    function routeDoctype() {
        const parts = (frappe.get_route() || []).map(scrub);
        return Object.keys(policies).find((doctype) => parts.includes(scrub(doctype))) || null;
    }

    function currentDoctype() {
        if (window.cur_frm?.doctype && policies[window.cur_frm.doctype]) {
            return window.cur_frm.doctype;
        }
        if (window.cur_list?.doctype && policies[window.cur_list.doctype]) {
            return window.cur_list.doctype;
        }
        return routeDoctype();
    }

    function config() {
        return policies[currentDoctype()] || { policy: "Standard" };
    }

    function blocksWrites(value) {
        return ["Disable Write Actions", "View Only"].includes(value?.policy);
    }

    function hide(element) {
        if (!element) return;
        element.classList.add("qorg-action-hidden");
        element.setAttribute("aria-hidden", "true");
        element.setAttribute("tabindex", "-1");
    }

    function hideAll(selector, root = document) {
        root.querySelectorAll(selector).forEach(hide);
    }

    function clearManagedHidden() {
        document.querySelectorAll(".qorg-action-hidden").forEach((element) => {
            element.classList.remove("qorg-action-hidden");
            element.removeAttribute("aria-hidden");
            element.removeAttribute("tabindex");
        });
    }

    function formIsReady(frm) {
        return Boolean(
            frm &&
            frm.doc &&
            frm.page &&
            frm.page.wrapper &&
            frm.toolbar &&
            frm.dashboard
        );
    }

    function applyFormPolicy(frm, value) {
        if (!formIsReady(frm)) return false;

        // Do not call disable_save before Form setup is complete. Native DocPerm
        // already blocks writes; this layer only controls action surfaces.
        frm.set_read_only?.();
        frm.clear_custom_buttons?.();
        frm.page.clear_primary_action?.();
        frm.page.clear_secondary_action?.();
        frm.page.clear_actions_menu?.();
        frm.page.clear_inner_toolbar?.();

        if (value.policy === "View Only") {
            frm.page.clear_menu?.();
        }
        return true;
    }

    function applyPagePolicy(value) {
        const page = window.cur_list?.page || window.cur_tree?.page;
        if (!page?.wrapper) return;

        page.clear_primary_action?.();
        page.clear_secondary_action?.();
        page.clear_actions_menu?.();
        if (value.policy === "View Only") {
            page.clear_inner_toolbar?.();
            page.clear_menu?.();
        }
    }

    function applyDomPolicy(value) {
        hideAll(
            ".page-head .primary-action, " +
            ".page-head .btn-primary, " +
            ".page-actions .btn-primary, " +
            ".standard-actions .btn-primary, " +
            ".grid-add-row, " +
            ".tree-toolbar .btn-primary, " +
            ".tree-node-toolbar .btn-primary, " +
            ".tree-actions .btn-primary, " +
            ".new-node, .add-child"
        );

        if (value.policy === "View Only") {
            hideAll(
                ".custom-actions, " +
                ".inner-toolbar, " +
                ".inner-group-button, " +
                ".actions-btn-group, " +
                ".menu-btn-group, " +
                ".workflow-button-group, " +
                ".page-actions .btn, " +
                ".standard-actions .btn"
            );
        }

        if (!value.allow_print) {
            hideAll(".print-btn, [data-label='Print'], [data-label='Print View']");
            hideAll(".form-sidebar .print-icon, .form-sidebar .octicon-print");
        }
        if (!value.allow_email) {
            hideAll("[data-label='Email'], [data-label='New Email'], .new-email");
        }
        if (!value.allow_comments) {
            hideAll(
                ".comment-box, .new-comment, .comment-input, " +
                ".timeline-comment-box, .form-comments, .comment-form, " +
                "[data-fieldname='comments']"
            );
        }
        if (!value.allow_attachments) {
            hideAll(
                ".attachments, .attachment-row, .form-attachments, " +
                ".attachment-btn, [data-label='Attachments']"
            );
        }
    }

    function applyPolicy() {
        clearManagedHidden();
        const value = config();
        if (!blocksWrites(value)) return;

        applyFormPolicy(window.cur_frm, value);
        applyPagePolicy(value);
        applyDomPolicy(value);
    }

    function scheduleApply() {
        if (scheduled) clearTimeout(scheduled);
        scheduled = setTimeout(() => {
            applyPolicy();
            requestAnimationFrame(applyPolicy);
            [100, 300, 700, 1400].forEach((delay) => setTimeout(applyPolicy, delay));
        }, 25);
    }

    async function reloadPolicies() {
        const response = await frappe.call({
            method: "qorg.qorg.enterprise_foundation.api.get_action_policies",
            silent: true,
        });
        policies = response.message || {};
        frappe.boot.qorg_action_policies = policies;
        scheduleApply();
    }

    frappe.realtime.on("qorg_model_policy_changed", reloadPolicies);
    frappe.router.on("change", () => reloadPolicies().catch(scheduleApply));
    $(document).on(
        "page-change form-refresh list-rendered form-load after_ajax",
        scheduleApply
    );

    // Observe only after the initial page is ready. Do not monkey-patch Page methods;
    // doing that during toolbar construction corrupts Frappe's own lifecycle.
    $(document).ready(() => {
        observer = new MutationObserver(scheduleApply);
        observer.observe(document.body, { childList: true, subtree: true });
        reloadPolicies().catch(scheduleApply);
    });
})();
