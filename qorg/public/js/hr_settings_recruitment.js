frappe.ui.form.on("HR Settings", {
    refresh(frm) {
        qorg_show_recruitment_weight_total(frm);
    },
    qorg_default_screening_weight(frm) {
        qorg_show_recruitment_weight_total(frm);
    },
    qorg_default_assessment_weight(frm) {
        qorg_show_recruitment_weight_total(frm);
    },
    validate(frm) {
        const screening = flt(frm.doc.qorg_default_screening_weight);
        const assessment = flt(frm.doc.qorg_default_assessment_weight);
        const total = flt(screening + assessment, 2);
        if (Math.abs(total - 100) > 0.01) {
            frappe.throw(__(
                "Default Screening and Assessment weights must total exactly 100%. Current total: {0}%.",
                [total]
            ));
        }
    }
});

function qorg_show_recruitment_weight_total(frm) {
    if (!frm.fields_dict.qorg_recruitment_defaults_tab) return;
    const screening = flt(frm.doc.qorg_default_screening_weight);
    const assessment = flt(frm.doc.qorg_default_assessment_weight);
    const total = flt(screening + assessment, 2);
    frm.set_intro(
        __("Default recruitment weight total: {0}%", [total]),
        Math.abs(total - 100) <= 0.01 ? "green" : "orange"
    );
}
