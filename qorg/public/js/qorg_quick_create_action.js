(() => {
    "use strict";
    let items = null;
    async function getItems() { if (items) return items; try { const response = await frappe.call({method: "qorg.qorg.design_system.api.get_quick_create_menu"}); items = response.message?.items || []; return items; } catch (error) { console.error("Q Org: unable to load Quick Create menu.", error); return []; } }
    function openCreateDialog(availableItems) {
        const dialog = new frappe.ui.Dialog({title: __("Create"), size: "large", fields: [{fieldname: "items", fieldtype: "HTML"}]});
        const wrapper = dialog.fields_dict.items.$wrapper.empty();
        const grid = $("<div>", {class: "qorg-quick-create-grid"});
        let currentGroup = null;
        availableItems.forEach((item) => {
            if (item.group !== currentGroup) { currentGroup = item.group; grid.append($("<div>", {class: "qorg-quick-create-group", text: __(currentGroup)})); }
            const button = $("<button>", {type: "button", class: "qorg-quick-create-item", title: item.description || __(item.label)});
            const icon = $("<span>", {class: "qorg-quick-create-item__icon"});
            if (item.icon && frappe.utils?.icon) icon.html(frappe.utils.icon(item.icon, "sm"));
            const text = $("<span>", {class: "qorg-quick-create-item__text"});
            text.append($("<span>", {class: "qorg-quick-create-item__label", text: __(item.label)}));
            if (item.description) text.append($("<span>", {class: "qorg-quick-create-item__description", text: __(item.description)}));
            button.append(icon, text).on("click", () => { dialog.hide(); frappe.new_doc(item.doctype); });
            grid.append(button);
        });
        wrapper.append(grid); dialog.show();
    }
    async function register() {
        const availableItems = await getItems();
        if (!availableItems.length) { window.qorgActionRail?.unregister("create"); return; }
        window.qorgActionRail?.register({id: "create", label: "New", tooltip: "Create", icon: "add", variant: "create", order: 10, onClick: () => openCreateDialog(availableItems)});
    }
    function start() { if (window.qorgActionRail) register(); else window.addEventListener("qorg-action-rail-ready", register, {once: true}); }
    frappe.router?.on?.("change", () => requestAnimationFrame(start));
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start, {once: true}); else start();
})();
