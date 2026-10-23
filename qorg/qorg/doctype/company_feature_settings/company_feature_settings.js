frappe.ui.form.on("Company Feature Settings", {
    refresh(frm) {
        frm.add_custom_button(__("Audit Configuration"), () => {
            frappe.call({
                method: "qorg.qorg.enterprise_foundation.api.audit_company_settings",
                args: {settings_name: frm.doc.name},
                freeze: true,
                callback: () => frm.reload_doc(),
            });
        });
    },
    mobile_attendance_mode(frm) {
        const mode = frm.doc.mobile_attendance_mode;
        frm.set_df_property("require_geolocation", "read_only", ["Geofenced Attendance", "Field Attendance"].includes(mode));
    },
});
