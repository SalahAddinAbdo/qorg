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

    async function register() {
        document.querySelectorAll("[data-qorg-language-action]").forEach((element) => element.remove());
        const data = await getConfig();
        if (!data.show_language_action) {
            window.qorgActionRail?.unregister("language");
            return;
        }
        window.qorgActionRail?.register({
            id: "language",
            label: "Language",
            icon: "language",
            order: 20,
            onClick: openDialog,
        });
    }

    frappe.router?.on?.("change", () => requestAnimationFrame(register));
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", register, {once: true});
    else register();
})();
