(() => {
    if (frappe.session.user === "Administrator") return;

    frappe.realtime.on("qorg_model_policy_changed", () => {
        frappe.show_alert({
            message: __("Access policies changed. Reloading permissions..."),
            indicator: "blue",
        });
        setTimeout(() => window.location.reload(), 500);
    });
})();
