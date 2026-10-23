(() => {
    const PROTECTED = new Set(["Read Only", "Feature Disabled", "Deprecated", "Restricted"]);
    const state = {
        policies: { ...(frappe.boot.qorg_model_policies || {}) },
        observer: null,
        running: false,
    };

    const scrub = (value) => (value || "")
        .toString()
        .toLowerCase()
        .replace(/[_\s]+/g, "-")
        .replace(/[^a-z0-9-]/g, "")
        .replace(/-+/g, "-")
        .replace(/^-|-$/g, "");

    const normalize = (value) => (value || "").replace(/\s+/g, " ").trim().toLowerCase();
    const MUTATION_WORDS = [
        "add", "new", "create", "save", "submit", "cancel", "delete", "rename", "merge",
        "update", "amend", "duplicate", "convert", "make", "close", "reopen", "edit",
    ];

    function doctypeFromRoute() {
        const route = frappe.get_route() || [];
        const candidates = [...route].reverse().map(scrub);
        for (const doctype of Object.keys(state.policies)) {
            if (candidates.includes(scrub(doctype))) return doctype;
        }
        return null;
    }

    function currentDoctype() {
        const routeDoctype = doctypeFromRoute();
        const formDoctype = window.cur_frm?.doctype;
        const listDoctype = window.cur_list?.doctype;
        if (formDoctype && state.policies[formDoctype]) return formDoctype;
        if (listDoctype && state.policies[listDoctype]) return listDoctype;
        return routeDoctype || formDoctype || listDoctype || null;
    }

    function currentPolicy() {
        const doctype = currentDoctype();
        return { doctype, policy: state.policies[doctype] || "Enabled" };
    }

    function isProtected(policy) {
        return PROTECTED.has(policy);
    }

    function clearDecorations() {
        document.body.classList.remove("qorg-model-write-blocked");
        document.body.removeAttribute("data-qorg-model-policy");
        document.querySelectorAll(".qorg-policy-hidden").forEach((element) => {
            element.classList.remove("qorg-policy-hidden");
            element.removeAttribute("aria-hidden");
            element.removeAttribute("tabindex");
        });
    }

    function hide(element) {
        if (!element) return;
        element.classList.add("qorg-policy-hidden");
        element.setAttribute("aria-hidden", "true");
        element.setAttribute("tabindex", "-1");
    }

    function labelOf(element) {
        return normalize(
            element?.getAttribute?.("data-label") ||
            element?.getAttribute?.("aria-label") ||
            element?.getAttribute?.("title") ||
            element?.textContent
        );
    }

    function isMutationAction(element) {
        if (!element) return false;
        if (element.matches(
            ".primary-action, .page-actions .btn-primary, .standard-actions .btn-primary, " +
            ".grid-add-row, .tree-toolbar .btn-primary, .tree-node-toolbar .btn-primary, " +
            ".tree-actions .btn-primary, .new-node, .add-child"
        )) return true;
        const label = labelOf(element);
        return MUTATION_WORDS.some((word) => label === word || label.startsWith(`${word} `));
    }

    function enforcePageApi(policy) {
        if (!isProtected(policy)) return;
        const pages = [window.cur_frm?.page, window.cur_list?.page].filter(Boolean);
        for (const page of pages) {
            page.clear_primary_action?.();
            page.clear_custom_actions?.();
            page.btn_primary?.hide?.();
            page.set_indicator?.(__(policy), policy === "Restricted" ? "red" : "orange");
        }
        if (window.cur_frm) {
            cur_frm.disable_save();
            cur_frm.set_read_only();
        }
    }

    function enforceDom(policy) {
        if (!isProtected(policy)) return;
        const alwaysHide = [
            ".page-head .primary-action",
            ".page-head .btn-primary",
            ".page-actions .btn-primary",
            ".standard-actions .btn-primary",
            ".grid-add-row",
            ".tree-toolbar .btn-primary",
            ".tree-node-toolbar .btn-primary",
            ".tree-actions .btn-primary",
            ".new-node",
            ".add-child",
            "[data-label^='Add ']",
            "[data-label^='New ']",
            "[data-label^='Create ']",
        ];
        document.querySelectorAll(alwaysHide.join(",")).forEach(hide);
        document.querySelectorAll(
            "button, a, .dropdown-item, .inner-group-button, .menu-item-label"
        ).forEach((element) => {
            if (isMutationAction(element)) hide(element);
        });
    }

    function applyPolicy() {
        if (state.running) return;
        state.running = true;
        try {
            if (frappe.session.user === "Administrator") {
                clearDecorations();
                return;
            }
            const { policy } = currentPolicy();
            clearDecorations();
            if (!isProtected(policy)) return;
            document.body.classList.add("qorg-model-write-blocked");
            document.body.dataset.qorgModelPolicy = policy;
            enforcePageApi(policy);
            enforceDom(policy);
        } finally {
            state.running = false;
        }
    }

    function schedule() {
        applyPolicy();
        requestAnimationFrame(applyPolicy);
        [40, 120, 350, 900, 1800].forEach((delay) => setTimeout(applyPolicy, delay));
    }

    function blockMutation(event) {
        if (frappe.session.user === "Administrator") return;
        const { doctype, policy } = currentPolicy();
        if (!doctype || !isProtected(policy)) return;
        const target = event.target.closest(
            "button, a, .dropdown-item, .inner-group-button, .menu-item-label"
        );
        if (!target || !isMutationAction(target)) return;
        event.preventDefault();
        event.stopImmediatePropagation();
        frappe.show_alert({ message: __(`${doctype} is ${policy}.`), indicator: "orange" });
    }

    async function refreshPolicies() {
        const result = await frappe.call({
            method: "qorg.qorg.enterprise_foundation.api.get_model_policies",
            silent: true,
        });
        state.policies = result.message || {};
        frappe.boot.qorg_model_policies = state.policies;
        schedule();
    }

    function startObserver() {
        state.observer?.disconnect();
        state.observer = new MutationObserver(() => applyPolicy());
        state.observer.observe(document.body, { childList: true, subtree: true });
    }

    document.addEventListener("click", blockMutation, true);
    frappe.router.on("change", schedule);
    frappe.realtime.on("qorg_model_policy_changed", refreshPolicies);
    $(document).on("page-change form-refresh list-rendered", schedule);
    startObserver();
    refreshPolicies().catch(schedule);
})();
