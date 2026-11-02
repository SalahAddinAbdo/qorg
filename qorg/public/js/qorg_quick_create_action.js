(() => {
    "use strict";

    let items = null;

    async function getItems() {
        if (items) return items;
        try {
            const response = await frappe.call({method: "qorg.qorg.design_system.api.get_quick_create_menu"});
            items = response.message?.items || [];
            return items;
        } catch (error) {
            console.error("Q Org: unable to load Quick Create menu.", error);
            return [];
        }
    }

    function openCreateDialog(availableItems) {
        const dialog = new frappe.ui.Dialog({title: __("Create"), size: "small", fields: [{fieldname: "items", fieldtype: "HTML"}]});
        const container = dialog.fields_dict.items.$wrapper.empty();
        let currentGroup = null;

        availableItems.forEach((item) => {
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

    async function register() {
        document.querySelectorAll("[data-qorg-create-action]").forEach((element) => element.remove());
        const availableItems = await getItems();
        if (!availableItems.length) {
            window.qorgActionRail?.unregister("create");
            return;
        }
        window.qorgActionRail?.register({
            id: "create",
            label: "Create",
            icon: "add",
            order: 10,
            onClick: () => openCreateDialog(availableItems),
        });
    }

    frappe.router?.on?.("change", () => requestAnimationFrame(register));
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", register, {once: true});
    else register();
})();
