(() => {
  if (!isWebFormPage()) return;

  frappe.call({
    method: "qorg.qorg.people_and_opportunities.portal_settings.get_web_form_design_settings",
    callback(response) {
      const settings = response.message || {};
      if (!Number(settings.enabled || 0)) return;
      applyDesign(settings);
    },
    error() {
      // Fail safely: Frappe's standard Web Form design remains fully usable.
    },
  });

  function isWebFormPage() {
    return Boolean(
      window.frappe?.web_form ||
      document.querySelector(".web-form-wrapper, .web-form-container, form[data-web-form]")
    );
  }

  function applyDesign(settings) {
    const body = document.body;
    body.classList.add("qorg-enhanced-web-form");
    if (Number(settings.sticky_actions || 0)) body.classList.add("qorg-sticky-webform-actions");
    if (Number(settings.hide_child_row_name || 0)) body.classList.add("qorg-hide-child-row-name");

    const root = document.documentElement;
    root.style.setProperty("--qwf-primary", safeColor(settings.primary_color, "#176b87"));
    root.style.setProperty("--qwf-secondary", safeColor(settings.secondary_color, "#0d4f67"));
    root.style.setProperty("--qwf-accent", safeColor(settings.accent_color, "#2f855a"));
    root.style.setProperty("--qwf-surface", safeColor(settings.surface_color, "#ffffff"));
    root.style.setProperty("--qwf-max-width", `${clamp(Number(settings.max_content_width || 1180), 760, 1600)}px`);

    onReady(() => {
      const container = getContainer();
      if (!container) return;
      if (Number(settings.show_hero_header || 0)) addHero(container, settings);
      if (Number(settings.show_privacy_notice || 0)) addNotice(container);
      cleanupChildNames(container);
      const observer = new MutationObserver(() => cleanupChildNames(container));
      observer.observe(container, { childList: true, subtree: true });
    });
  }

  function getContainer() {
    return (
      document.querySelector("main .container") ||
      document.querySelector(".page-content-wrapper .container") ||
      document.querySelector("main.container") ||
      document.querySelector(".web-form-container") ||
      document.querySelector("main")
    );
  }

  function addHero(container, settings) {
    if (container.querySelector(".qorg-global-webform-hero")) return;
    const title = document.querySelector(".web-form-header h1, .page-header h1, .web-form-head h1")?.textContent?.trim() || document.title;
    const introduction = document.querySelector(".web-form-introduction, .introduction")?.textContent?.trim() || __("Complete the information below and review it carefully before submission.");
    const hero = document.createElement("section");
    hero.className = "qorg-global-webform-hero";
    const logo = settings.logo ? `<img src="${escapeAttribute(settings.logo)}" alt="">` : "";
    const brand = settings.company_name ? `<div class="qorg-global-webform-brand">${logo}<strong>${escapeHtml(settings.company_name)}</strong></div>` : "";
    hero.innerHTML = `
      <div class="qorg-global-webform-hero-content">
        <div class="qorg-global-webform-eyebrow">${escapeHtml(__("Online Form"))}</div>
        <h1>${escapeHtml(title)}</h1>
        <p>${escapeHtml(introduction)}</p>
      </div>${brand}`;
    container.prepend(hero);
  }

  function addNotice(container) {
    if (container.querySelector(".qorg-global-webform-notice")) return;
    const form = container.querySelector(".web-form-wrapper, .web-form-container, .web-form");
    if (!form) return;
    const notice = document.createElement("div");
    notice.className = "qorg-global-webform-notice";
    notice.innerHTML = `<span class="qorg-global-webform-notice-icon" aria-hidden="true">✓</span><span>${escapeHtml(__("Your information is handled according to the form's purpose and the organization's access controls. Review all required fields before saving or submitting."))}</span>`;
    form.prepend(notice);
  }

  function cleanupChildNames(container) {
    if (!document.body.classList.contains("qorg-hide-child-row-name")) return;
    container.querySelectorAll('.grid-row-form [data-fieldname="name"], .grid-row-form .form-group[data-fieldname="name"]').forEach((element) => {
      const control = element.closest(".frappe-control, .form-group") || element;
      control.hidden = true;
      control.setAttribute("aria-hidden", "true");
    });
  }

  function onReady(callback) {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", callback, { once: true });
    } else {
      callback();
    }
  }

  function safeColor(value, fallback) {
    const color = String(value || "").trim();
    return /^#[0-9a-f]{3,8}$/i.test(color) ? color : fallback;
  }

  function clamp(value, min, max) {
    return Math.min(Math.max(Number.isFinite(value) ? value : min, min), max);
  }

  function escapeHtml(value) {
    const div = document.createElement("div");
    div.textContent = String(value || "");
    return div.innerHTML;
  }

  function escapeAttribute(value) {
    return escapeHtml(value).replace(/`/g, "&#96;");
  }
})();
