frappe.ui.form.on("External Opportunity", {
    setup(frm) {
        frm.set_query("opportunity_type", () => ({ filters: { enabled: 1 } }));
        frm.set_query("job_opening", () => ({ filters: { status: "Open" } }));
    },
    refresh(frm) {
        if (frm.is_new()) return;
        const add = (label, status) => frm.add_custom_button(
            __(label),
            () => frappe.call({
                method: "qorg.qorg.people_and_opportunities.api.transition_opportunity",
                args: { name: frm.doc.name, status },
                freeze: true,
                callback: () => frm.reload_doc()
            }),
            __("Status")
        );
        if (frm.doc.status === "Draft") add("Submit for Review", "Under Review");
        if (frm.doc.status === "Approved") add("Publish", "Published");
        if (frm.doc.status === "Published") add("Close", "Closed");
    }
});
