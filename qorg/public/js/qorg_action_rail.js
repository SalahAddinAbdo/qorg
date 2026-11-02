(() => {
    "use strict";

    const ROOT_ID = "qorg-action-rail";
    const STORAGE_KEY = "qorg-action-rail-collapsed-v1";
    const actions = new Map();

    const icons = {
        add: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 5v14M5 12h14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>',
        language: '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M3.5 12h17M12 3c2.6 2.5 4 5.5 4 9s-1.4 6.5-4 9c-2.6-2.5-4-5.5-4-9s1.4-6.5 4-9Z" fill="none" stroke="currentColor" stroke-width="1.8"/></svg>',
        toggle: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m9 6 6 6-6 6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    };

    const isCollapsed = () => localStorage.getItem(STORAGE_KEY) === "1";

    function setCollapsed(collapsed) {
        localStorage.setItem(STORAGE_KEY, collapsed ? "1" : "0");
        render();
    }

    function ensureRoot() {
        let root = document.getElementById(ROOT_ID);
        if (root) return root;
        root = document.createElement("aside");
        root.id = ROOT_ID;
        root.className = "qorg-action-rail";
        root.setAttribute("aria-label", __("Quick actions"));
        document.body.append(root);
        return root;
    }

    function render() {
        const root = ensureRoot();
        const entries = [...actions.values()]
            .filter((action) => action.visible !== false)
            .sort((a, b) => (a.order || 100) - (b.order || 100));

        root.replaceChildren();
        root.hidden = entries.length === 0;
        if (!entries.length) return;

        const collapsed = isCollapsed();
        root.classList.toggle("is-collapsed", collapsed);

        const toggle = document.createElement("button");
        toggle.type = "button";
        toggle.className = "qorg-action-rail__toggle";
        toggle.setAttribute("aria-expanded", String(!collapsed));
        toggle.setAttribute("aria-controls", "qorg-action-rail-items");
        toggle.title = collapsed ? __("Show quick actions") : __("Hide quick actions");
        toggle.innerHTML = icons.toggle;
        toggle.addEventListener("click", () => setCollapsed(!collapsed));
        root.append(toggle);

        const items = document.createElement("div");
        items.id = "qorg-action-rail-items";
        items.className = "qorg-action-rail__items";
        items.hidden = collapsed;

        entries.forEach((action) => {
            const button = document.createElement("button");
            button.type = "button";
            button.className = `qorg-action-rail__action is-${action.variant || "neutral"}`;
            button.dataset.qorgAction = action.id;
            button.title = __(action.tooltip || action.label);
            button.setAttribute("aria-label", __(action.tooltip || action.label));
            button.innerHTML = `<span class="qorg-action-rail__icon">${icons[action.icon] || icons.add}</span><span class="qorg-action-rail__label">${__(action.label)}</span>`;
            button.addEventListener("click", action.onClick);
            items.append(button);
        });
        root.append(items);
    }

    function register(action) {
        if (!action?.id || typeof action.onClick !== "function") return;
        actions.set(action.id, action);
        render();
    }

    function unregister(id) {
        actions.delete(id);
        render();
    }

    window.qorgActionRail = {register, unregister, render};
    window.dispatchEvent(new CustomEvent("qorg-action-rail-ready"));

    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", render, {once: true});
    else render();
})();
