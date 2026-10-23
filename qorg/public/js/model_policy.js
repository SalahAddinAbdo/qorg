(() => {
    "use strict";

    const VERSION = "1.3.4";
    if (window.qorgModelPolicyVersion === VERSION) return;
    window.qorgModelPolicyVersion = VERSION;

    if (frappe.session.user === "Administrator") return;

    let policies = { ...(frappe.boot.qorg_action_policies || {}) };
    let timer = null;
    let observer = null;

    const slug = (value) => (value || "")
        .toString()
        .toLowerCase()
        .replace(/[_\s]+/g, "-")
        .replace(/[^a-z0-9-]/g, "")
        .replace(/-+/g, "-")
        .replace(/^-|-$/g, "");

    function routeDoctype() {
        const route = (frappe.get_route() || []).map(slug);
        return Object.keys(policies).find((doctype) => route.includes(slug(doctype))) || null;
    }

    function currentDoctype() {
        if (window.cur_frm?.doctype && policies[window.cur_frm.doctype]) return window.cur_frm.doctype;
        if (window.cur_list?.doctype && policies[window.cur_list.doctype]) return window.cur_list.doctype;
        return routeDoctype();
    }

    function currentPolicy() {
        return policies[currentDoctype()] || { policy: "Standard" };
    }

    function hide(element) {
        if (!element) return;
        element.classList.add("qorg-action-hidden-v134");
        element.setAttribute("aria-hidden", "true");
        element.setAttribute("tabindex", "-1");
    }

    function hideAll(selector) {
        document.querySelectorAll(selector).forEach(hide);
    }

    function restoreManagedElements() {
        document.querySelectorAll(".qorg-action-hidden-v134").forEach((element) => {
            element.classList.remove("qorg-action-hidden-v134");
            element.removeAttribute("aria-hidden");
            element.removeAttribute("tabindex");
        });
    }

    function applyPolicy() {
        restoreManagedElements();
        const policy = currentPolicy();
        if (!["Disable Write Actions", "View Only"].includes(policy.policy)) return;

        // Native Custom DocPerm is authoritative for data writes. This script only
        // controls visible action surfaces and never calls Form.disable_save().
        hideAll(
            ".page-head .primary-action, .page-actions .btn-primary, " +
            ".standard-actions .btn-primary, .grid-add-row, " +
            ".tree-toolbar .btn-primary, .tree-node-toolbar .btn-primary, " +
            ".tree-actions .btn-primary, .new-node, .add-child"
        );

        if (policy.policy === "View Only") {
            hideAll(
                ".custom-actions, .inner-toolbar, .inner-group-button, " +
                ".actions-btn-group, .menu-btn-group, .workflow-button-group, " +
                ".page-actions .btn, .standard-actions .btn, " +
                ".page-head .dropdown, .page-head .btn-group"
            );
        }

        if (!Number(policy.allow_print)) {
            hideAll(".print-btn, [data-label='Print'], [data-label='Print View'], [title='Print']");
        }
        if (!Number(policy.allow_email)) {
            hideAll("[data-label='Email'], [data-label='New Email'], .new-email");
        }
        if (!Number(policy.allow_comments)) {
            hideAll(
                ".comment-box, .new-comment, .comment-input, .timeline-comment-box, " +
                ".form-comments, .comment-form, .comment-section"
            );
        }
        if (!Number(policy.allow_attachments)) {
            hideAll(
                ".attachments, .attachment-row, .form-attachments, .attachment-btn, " +
                "[data-label='Attachments'], .sidebar-section.attachments"
            );
        }
    }

    function scheduleApply() {
        if (timer) clearTimeout(timer);
        timer = setTimeout(() => {
            applyPolicy();
            requestAnimationFrame(applyPolicy);
            [100, 300, 700, 1500].forEach((delay) => setTimeout(applyPolicy, delay));
        }, 20);
    }

    async function refreshPolicies() {
        const response = await frappe.call({
            method: "qorg.qorg.enterprise_foundation.api.get_action_policies",
            silent: true,
        });
        policies = response.message || {};
        frappe.boot.qorg_action_policies = policies;
        scheduleApply();
    }

    frappe.realtime.on("qorg_model_policy_changed", refreshPolicies);
    frappe.router.on("change", () => refreshPolicies().catch(scheduleApply));
    $(document).on("page-change form-refresh list-rendered after_ajax", scheduleApply);

    $(document).ready(() => {
        observer = new MutationObserver(scheduleApply);
        observer.observe(document.body, { childList: true, subtree: true });
        refreshPolicies().catch(scheduleApply);
        console.info(`[QOrg] model policy client ${VERSION} loaded`);
    });
})();
