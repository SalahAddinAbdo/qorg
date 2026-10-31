(() => {
  "use strict";
  const marker = "data-qorg-language-action";
  const call = (method, args = {}) => frappe.call({ method, args }).then(response => response.message || {});

  function findHost() {
    const selectors = [
      ".desk-sidebar .sidebar-header",
      ".module-sidebar .sidebar-header",
      "[data-sidebar] .sidebar-header",
      ".desk-sidebar .sidebar-footer",
      ".module-sidebar .sidebar-footer",
      ".page-head .page-actions",
      ".page-head .standard-actions",
      ".navbar .navbar-nav",
    ];
    for (const selector of selectors) {
      const host = document.querySelector(selector);
      if (host) return host;
    }
    return null;
  }

  async function openLanguageDialog() {
    const data = await call("qorg.qorg.design_system.api.get_available_languages");
    const dialog = new frappe.ui.Dialog({
      title: __("Language"),
      fields: [{
        fieldname: "language",
        fieldtype: "Select",
        label: __("Language"),
        options: (data.languages || []).map(item => ({
          label: item.language_name,
          value: item.language_code,
        })),
        default: data.current,
        reqd: 1,
      }],
      primary_action_label: __("Apply"),
      primary_action: async values => {
        await call("qorg.qorg.design_system.api.set_current_user_language", values);
        window.location.reload();
      },
    });
    dialog.show();
  }

  function mount() {
    if (document.querySelector(`[${marker}]`)) return;
    const host = findHost();
    if (!host) return;
    const button = document.createElement("button");
    button.type = "button";
    button.className = "btn btn-default btn-sm";
    button.setAttribute(marker, "1");
    button.setAttribute("aria-label", __("Language"));
    button.title = __("Language");
    button.innerHTML = `${frappe.utils.icon("globe", "sm")}<span class="hidden-xs">${__("Language")}</span>`;
    button.addEventListener("click", openLanguageDialog);
    host.append(button);
  }

  frappe.router?.on?.("change", () => window.requestAnimationFrame(mount));
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", mount, { once: true });
  } else {
    mount();
  }
})();
