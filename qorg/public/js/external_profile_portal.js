frappe.ready(async () => {
    const root = document.getElementById("external-profile-app");
    if (!root) return;
    const name = root.dataset.person;
    if (!name) {
        root.innerHTML = '<div class="alert alert-info">No profile is linked to this account yet.</div>';
        return;
    }

    const result = await frappe.call({
        method: "qorg.qorg.people_and_opportunities.portal_api.get_profile",
        args: { name }
    });
    render(result.message || {});

    function esc(value) {
        return frappe.utils.escape_html(value || "");
    }

    function render(profile) {
        root.innerHTML = `
            <div class="card shadow-sm">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-center mb-3">
                        <div>
                            <h4 class="mb-1">${esc(profile.full_name)}</h4>
                            <div class="text-muted">${esc(profile.professional_title)}</div>
                        </div>
                        <span class="badge badge-primary">${profile.profile_completion || 0}% complete</span>
                    </div>
                    <div class="progress mb-4"><div class="progress-bar" style="width:${profile.profile_completion || 0}%"></div></div>
                    <form id="profile-form">
                        <div class="row">
                            ${input("full_name", "Full Name", profile.full_name, true)}
                            ${input("name_in_arabic", "Name in Arabic", profile.name_in_arabic)}
                            ${input("professional_title", "Professional Title", profile.professional_title)}
                            ${input("primary_email", "Primary Email", profile.primary_email, true, "email")}
                            ${input("secondary_email", "Secondary Email", profile.secondary_email, false, "email")}
                            ${input("mobile_no", "Mobile Number", profile.mobile_no)}
                            ${input("alternative_mobile_no", "Alternative Mobile", profile.alternative_mobile_no)}
                            ${input("linkedin_url", "LinkedIn URL", profile.linkedin_url, false, "url")}
                            ${input("portfolio_url", "Portfolio URL", profile.portfolio_url, false, "url")}
                            ${textarea("professional_summary", "Professional Summary", profile.professional_summary)}
                            ${textarea("career_objective", "Career Objective", profile.career_objective)}
                        </div>
                        <div class="alert alert-light border">
                            Education: ${profile.education_count || 0} &nbsp;|&nbsp;
                            Experience: ${profile.experience_count || 0} &nbsp;|&nbsp;
                            Training: ${profile.training_count || 0} &nbsp;|&nbsp;
                            Languages: ${profile.language_count || 0} &nbsp;|&nbsp;
                            Skills: ${profile.skill_count || 0}
                        </div>
                        <button class="btn btn-primary" type="submit">Save Profile</button>
                        <span id="profile-message" class="ml-3"></span>
                    </form>
                </div>
            </div>`;

        document.getElementById("profile-form").addEventListener("submit", async (event) => {
            event.preventDefault();
            const form = new FormData(event.currentTarget);
            const values = Object.fromEntries(form.entries());
            const message = document.getElementById("profile-message");
            message.textContent = "Saving...";
            const saved = await frappe.call({
                method: "qorg.qorg.people_and_opportunities.portal_api.update_profile",
                type: "POST",
                args: { name, values: JSON.stringify(values) },
                freeze: true
            });
            message.textContent = "Saved";
            render(saved.message || profile);
        });
    }

    function input(name, label, value, required = false, type = "text") {
        return `<div class="col-md-6 form-group"><label>${label}</label><input class="form-control" name="${name}" type="${type}" value="${esc(value)}" ${required ? "required" : ""}></div>`;
    }

    function textarea(name, label, value) {
        return `<div class="col-12 form-group"><label>${label}</label><textarea class="form-control" rows="4" name="${name}">${esc(value)}</textarea></div>`;
    }
});
