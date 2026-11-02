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

    function openCreateDialog(items) {
        const dialog = new frappe.ui.Dialog({title: __("Create"), size: "small", fields: [{fieldname: "items", fieldtype: "HTML"}]});
        const container = dialog.fields_dict.items.$wrapper.empty();
        let currentGroup = null;

        items.forEach((item) => {
            if (item.group !== currentGroup) {
                currentGroup = item.group;
                container.append($("<div>", {class: "text-muted small mt-3 mb-1", text: __(currentGroup)}));
            }
            const button = $("<button>", {type: "button", class: "btn btn-default btn-sm w-100 text-start mb-1"});
            if (item.icon && frappe.utils?.icon) button.append($(frappe.utils.icon(item.icon, "sm")).addClass("me-2"));
            button.append(document.createTextNode(__(item.label)));
            if (item.description) button.attr("title", item.description);
            button.on("click", () => {
                dialog.hide();
                frappe.new_doc(item.doctype);
            });
            container.append(button);
        });
        dialog.show();
    }

    async function mount() {
        const host = document.querySelector(".page-head .page-actions") || document.querySelector(".navbar .navbar-nav");
        if (!host || host.querySelector("[data-qorg-create-action]")) return;
        const items = await getItems();
        if (!items.length) return;

        const button = document.createElement("button");
        button.type = "button";
        button.className = "btn btn-primary btn-sm";
        button.dataset.qorgCreateAction = "1";
        button.textContent = __("Create");
        button.addEventListener("click", () => openCreateDialog(items));
        host.append(button);
    }

    frappe.router?.on?.("change", () => requestAnimationFrame(mount));
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", mount, {once: true});
    else mount();
})();
