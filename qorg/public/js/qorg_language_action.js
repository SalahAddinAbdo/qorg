(() => {
    "use strict";

    const call = (method, args = {}) => frappe.call({method, args}).then((response) => response.message || {});
    let languageConfig = null;

    async function openLanguageDialog() {
        const data = languageConfig || await call("qorg.qorg.design_system.api.get_available_languages");
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

    async function mountLanguageAction() {
        if (document.querySelector("[data-qorg-language-action]")) return;
        languageConfig = await call("qorg.qorg.design_system.api.get_available_languages");
        if (!languageConfig.show_language_action) return;

        const host = document.querySelector(".desk-sidebar .sidebar-header,.module-sidebar .sidebar-header,.page-head .page-actions,.navbar .navbar-nav");
        if (!host) return;

        const button = document.createElement("button");
        button.type = "button";
        button.className = "btn btn-default btn-sm";
        button.dataset.qorgLanguageAction = "1";
        button.textContent = __("Language");
        button.addEventListener("click", openLanguageDialog);
        host.append(button);
    }

    frappe.router?.on?.("change", () => requestAnimationFrame(mountLanguageAction));
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", mountLanguageAction, {once: true});
    else mountLanguageAction();
})();
