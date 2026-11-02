(() => {
    "use strict";

    const call = (method, args = {}) => frappe.call({method, args}).then((response) => response.message || {});
    let config = null;

    async function getConfig() {
        if (!config) config = await call("qorg.qorg.design_system.api.get_available_languages");
        return config;
    }

    async function openDialog() {
        const data = await getConfig();
        const dialog = new frappe.ui.Dialog({
            title: __("Language"),
            fields: [{
                fieldname: "language",
                fieldtype: "Select",
                label: __("Language"),
                options: data.languages.map((item) => ({label: item.language_name, value: item.language_code})),
                default: data.current,
                reqd: 1,
            }],
            primary_action_label: __("Apply"),
            primary_action: async (values) => {
                await call("qorg.qorg.design_system.api.set_current_user_language", values);
                location.reload();
            },
        });
        dialog.show();
    }

    async function mount() {
        if (document.querySelector("[data-qorg-language-action]")) return;
        const data = await getConfig();
        if (!data.show_language_action) return;

        const host = document.querySelector(".desk-sidebar .sidebar-header,.module-sidebar .sidebar-header,.page-head .page-actions,.navbar .navbar-nav");
        if (!host) return;

        const button = document.createElement("button");
        button.type = "button";
        button.className = "btn btn-default btn-sm";
        button.dataset.qorgLanguageAction = "1";
        button.textContent = __("Language");
        button.addEventListener("click", openDialog);
        host.append(button);
    }

    frappe.router?.on?.("change", () => requestAnimationFrame(mount));
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", mount, {once: true});
    else mount();
})();
