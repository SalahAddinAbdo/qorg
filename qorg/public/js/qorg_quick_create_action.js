(() => {
    "use strict";

    async function getItems() {
        try {
            const response = await frappe.call({method: "qorg.qorg.design_system.api.get_quick_create_menu"});
            return response.message?.items || [];
        } catch (error) {
            console.error("Q Org: unable to load Quick Create menu.", error);
            return [];
        }
    }

    function closeMenus(except) {
        document.querySelectorAll("[data-qorg-create-menu]").forEach((menu) => {
            if (menu !== except) menu.hidden = true;
        });
    }

    async function mountCreateAction() {
        if (document.querySelector("[data-qorg-create-action]")) return;
        const items = await getItems();
        if (!items.length) return;

        const host = document.querySelector(".desk-sidebar .sidebar-header,.module-sidebar .sidebar-header,.page-head .page-actions,.navbar .navbar-nav");
        if (!host) return;

        const wrapper = document.createElement("div");
        wrapper.className = "dropdown qorg-create-action";
        wrapper.dataset.qorgCreateAction = "1";

        const button = document.createElement("button");
        button.type = "button";
        button.className = "btn btn-primary btn-sm";
        button.textContent = __("Create");
        button.setAttribute("aria-haspopup", "menu");
        button.setAttribute("aria-expanded", "false");

        const menu = document.createElement("div");
        menu.className = "dropdown-menu show";
        menu.dataset.qorgCreateMenu = "1";
        menu.hidden = true;
        menu.setAttribute("role", "menu");

        let currentGroup = null;
        items.forEach((item) => {
            if (item.group !== currentGroup) {
                currentGroup = item.group;
                const heading = document.createElement("div");
                heading.className = "dropdown-header";
                heading.textContent = __(currentGroup);
                menu.append(heading);
            }

            const action = document.createElement("button");
            action.type = "button";
            action.className = "dropdown-item";
            action.setAttribute("role", "menuitem");
            action.textContent = __(item.label);
            action.title = item.description || "";
            action.addEventListener("click", () => {
                menu.hidden = true;
                button.setAttribute("aria-expanded", "false");
                frappe.new_doc(item.doctype);
            });
            menu.append(action);
        });

        button.addEventListener("click", (event) => {
            event.stopPropagation();
            const willOpen = menu.hidden;
            closeMenus(menu);
            menu.hidden = !willOpen;
            button.setAttribute("aria-expanded", String(willOpen));
        });

        document.addEventListener("click", () => {
            menu.hidden = true;
            button.setAttribute("aria-expanded", "false");
        });

        wrapper.append(button, menu);
        host.append(wrapper);
    }

    frappe.router?.on?.("change", () => requestAnimationFrame(mountCreateAction));
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", mountCreateAction, {once: true});
    else mountCreateAction();
})();
