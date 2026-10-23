(() => {
    const WRITE_POLICIES = new Set(["Read Only", "Feature Disabled", "Deprecated", "Restricted"]);
    const state = {
        policies: { ...(frappe.boot.qorg_model_policies || {}) },
        observer: null,
        applying: false,
        last_doctype: null,
    };

    const normalize = (value) => (value || "").replace(/\s+/g, " ").trim().toLowerCase();
    const MUTATING_LABELS = [
        "add", "new", "create", "save", "submit", "cancel", "delete", "rename", "merge",
        "update", "amend", "duplicate", "convert to non-group", "make", "close", "reopen",
    ];

    function currentDoctype() {
        if (window.cur_frm?.doctype) return window.cur_frm.doctype;
        if (window.cur_list?.doctype) return window.cur_list.doctype;
        const route = frappe.get_route() || [];
        if (["List", "Form", "Tree", "query-report", "report"].includes(route[0])) return route[1];
        return null;
    }

    function currentPolicy() {
        const doctype = currentDoctype();
        return { doctype, policy: state.policies[doctype] || "Enabled" };
    }

    function isProtected(policy) {
        return WRITE_POLICIES.has(policy);
    }

    function markPage(policy) {
        document.body.dataset.qorgModelPolicy = policy;
        document.body.classList.toggle("qorg-model-write-blocked", isProtected(policy));
    }

    function isMutatingElement(element) {
        if (!element) return false;
        const label = normalize(
            element.getAttribute("data-label") ||
            element.getAttribute("aria-label") ||
            element.textContent
        );
        return MUTATING_LABELS.some((token) => label === token || label.startsWith(`${token} `));
    }

    function hideElement(element) {
        if (!element) return;
        element.classList.add("qorg-policy-hidden");
        element.setAttribute("aria-hidden", "true");
        element.setAttribute("tabindex", "-1");
    }

    function enforceButtons(policy) {
        if (!isProtected(policy)) return;
        const selectors = [
            ".page-actions .btn-primary",
            ".standard-actions .btn-primary",
            ".custom-actions .btn-primary",
            ".list-row-col .btn-primary",
            ".tree-toolbar .btn-primary",
            ".tree-node-toolbar .btn-primary",
            ".grid-add-row",
            "button[data-label]",
            "a[data-label]",
            ".dropdown-item",
            ".inner-group-button",
        ];
        document.querySelectorAll(selectors.join(",")).forEach((element) => {
            if (element.matches(".page-actions .btn-primary, .standard-actions .btn-primary, .grid-add-row") || isMutatingElement(element)) {
                hideElement(element);
            }
        });
    }

    function enforceForm(policy) {
        if (!window.cur_frm || !isProtected(policy)) return;
        cur_frm.disable_save();
        cur_frm.set_read_only();
        cur_frm.page.clear_primary_action();
        cur_frm.page.clear_custom_actions?.();
        cur_frm.page.set_indicator(__(policy), policy === "Restricted" ? "red" : "orange");
    }

    function enforceList(policy) {
        if (!window.cur_list || !isProtected(policy)) return;
        cur_list.page.clear_primary_action();
        cur_list.page.clear_custom_actions?.();
        cur_list.page.set_indicator(__(policy), policy === "Restricted" ? "red" : "orange");
    }

    function applyPolicy() {
        if (state.applying) return;
        state.applying = true;
        try {
            const { doctype, policy } = currentPolicy();
            state.last_doctype = doctype;
            markPage(policy);
            enforceForm(policy);
            enforceList(policy);
            enforceButtons(policy);
        } finally {
            state.applying = false;
        }
    }

    function scheduleApply() {
        applyPolicy();
        requestAnimationFrame(applyPolicy);
        setTimeout(applyPolicy, 80);
        setTimeout(applyPolicy, 300);
        setTimeout(applyPolicy, 900);
    }

    function blockMutation(event) {
        const { doctype, policy } = currentPolicy();
        if (!doctype || !isProtected(policy)) return;
        const target = event.target.closest("button, a, .dropdown-item");
        if (!target || !isMutatingElement(target)) return;
        event.preventDefault();
        event.stopImmediatePropagation();
        frappe.show_alert({ message: __(`${doctype} is ${policy}.`), indicator: "orange" });
    }

    function startObserver() {
        if (state.observer) state.observer.disconnect();
        state.observer = new MutationObserver(() => applyPolicy());
        state.observer.observe(document.body, { childList: true, subtree: true, attributes: false });
    }

    async function refreshPolicies() {
        try {
            const result = await frappe.call({
                method: "qorg.qorg.enterprise_foundation.api.get_model_policies",
                silent: true,
            });
            state.policies = result.message || {};
            frappe.boot.qorg_model_policies = state.policies;
        } finally {
            scheduleApply();
        }
    }

    document.addEventListener("click", blockMutation, true);
    frappe.router.on("change", scheduleApply);
    frappe.realtime.on("qorg_model_policy_changed", refreshPolicies);
    $(document).on("page-change form-refresh list-rendered", scheduleApply);
    startObserver();
    scheduleApply();
})();
