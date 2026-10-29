(() => {
  const form = document.getElementById("qorg-application-form");
  if (!form || form.dataset.bound === "1") return;
  form.dataset.bound = "1";
  const message = document.getElementById("qorg-application-message");
  const button = form.querySelector('button[type="submit"]');

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    message.className = "qorg-form-message";
    message.textContent = "";
    if (!form.reportValidity()) return;

    const data = new FormData(form);
    const hours = data.get("hours_per_week");
    if (hours && (Number(hours) < 0 || Number(hours) > 168)) {
      message.className = "qorg-form-message is-error";
      message.textContent = __("Hours available per week must be between 0 and 168.");
      return;
    }

    button.disabled = true;
    button.textContent = __("Submitting...");
    try {
      const response = await frappe.call({
        method: "qorg.qorg.people_and_opportunities.portal.submit_opportunity_application",
        args: {
          opportunity_route: form.dataset.route,
          motivation: data.get("motivation") || "",
          availability_start_date: data.get("availability_start_date") || null,
          hours_per_week: hours || null,
          consent: data.get("consent") ? 1 : 0,
        },
        freeze: true,
        freeze_message: __("Submitting your application..."),
      });
      message.className = "qorg-form-message is-success";
      message.textContent = response.message.message || __("Application submitted successfully.");
      form.reset();
      window.setTimeout(() => { window.location.href = "/my-applications"; }, 1200);
    } catch (error) {
      message.className = "qorg-form-message is-error";
      message.textContent = error?.message || __("The application could not be submitted. Please review your profile and try again.");
    } finally {
      button.disabled = false;
      button.textContent = __("Submit Application");
    }
  });
})();
