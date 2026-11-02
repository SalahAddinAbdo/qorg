(() => {
    "use strict";

    const ROOT_ID = "qorg-action-rail";
    const STORAGE_KEY = "qorg-action-rail-collapsed-v1";
    const actions = new Map();

    const iconMarkup = (name, size = "sm") => {
        if (window.frappe?.utils?.icon) return frappe.utils.icon(name, size);
        return `<span aria-hidden="true">${name === "chevron-right" ? "›" : "•"}</span>`;
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
        toggle.innerHTML = iconMarkup("chevron-right", "sm");
        toggle.addEventListener("click", () => setCollapsed(!collapsed));
        root.append(toggle);

        const items = document.createElement("div");
        items.id = "qorg-action-rail-items";
        items.className = "qorg-action-rail__items";
        items.hidden = collapsed;

        entries.forEach((action) => {
            const button = document.createElement("button");
            button.type = "button";
            button.className = "qorg-action-rail__action";
            button.dataset.qorgAction = action.id;
            button.title = __(action.label);
            button.setAttribute("aria-label", __(action.label));
            button.innerHTML = iconMarkup(action.icon || "add", "md");
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

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", render, {once: true});
    } else {
        render();
    }
})();
