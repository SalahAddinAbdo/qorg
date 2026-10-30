(() => {
  "use strict";
  const root = document.documentElement;
  const key = (value, fallback = "standard") => String(value || fallback).trim().toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
  const onReady = (fn) => document.readyState === "loading" ? document.addEventListener("DOMContentLoaded", fn, { once: true }) : fn();

  function applyVariables(config) {
    Object.entries(config.css_variables || {}).forEach(([name, value]) => {
      if (name.startsWith("--qorg-") && typeof value === "string") root.style.setProperty(name, value);
    });
  }

  function applyPublicAttributes(config) {
    root.dataset.qorgWebForm = key(config.web_form_presentation, "enterprise");
    root.dataset.qorgPortal = key(config.portal_presentation, "enterprise");
    root.dataset.qorgPublicCards = key(config.public_card_style, "elevated");
    root.dataset.qorgPublicValidation = config.public_validation_summary ? "1" : "0";
    root.dataset.qorgPublicSuccess = key(config.public_success_presentation, "celebratory-minimal");
    root.dataset.qorgPublicMobileActions = config.public_mobile_sticky_actions ? "1" : "0";
    root.dataset.qorgWebFormStickyActions = config.web_form_sticky_actions ? "1" : "0";
    root.dataset.qorgHideTechnicalChildRowName = config.web_form_hide_technical_child_row_name ? "1" : "0";
  }

  function buildLogin(config) {
    const login = document.querySelector(".for-login");
    const card = login?.querySelector(".page-card");
    if (!login || !card || config.login_experience_style === "Frappe Standard") return;

    root.classList.add("qorg-login-enhanced");
    root.dataset.qorgLoginExperience = key(config.login_experience_style, "qorg-executive");
    root.dataset.qorgLoginDensity = key(config.login_form_density, "comfortable");
    root.dataset.qorgLoginAlignment = key(config.login_card_alignment, "auto");
    root.dataset.qorgLoginMobile = key(config.login_mobile_visual_policy, "hide");
    card.dataset.qorgLoginCard = "1";

    if (!card.querySelector(".qorg-login-visual")) {
      const visual = document.createElement("aside");
      visual.className = "qorg-login-visual";
      visual.setAttribute("aria-hidden", "true");
      if (config.login_visual_source === "Managed Image" && config.login_visual_image) {
        visual.style.backgroundImage = `linear-gradient(rgba(8,35,47,.24),rgba(8,35,47,.72)),url(${JSON.stringify(String(config.login_visual_image))})`;
      } else {
        visual.dataset.gradient = key(config.login_visual_gradient, "qorg-blue");
      }
      const copy = document.createElement("div"); copy.className = "qorg-login-visual-copy";
      const brand = document.createElement("span"); brand.className = "qorg-login-brand"; brand.textContent = "QOrg";
      const title = document.createElement("h2"); title.textContent = config.login_welcome_title || "Welcome to QOrg";
      const subtitle = document.createElement("p"); subtitle.textContent = config.login_welcome_subtitle || "Integrated, secure and efficient enterprise management.";
      copy.append(brand, title, subtitle); visual.append(copy); card.append(visual);
    }

    const body = card.querySelector(".page-card-body") || card;
    if (config.login_show_trust_message && config.login_trust_message && !card.querySelector(".qorg-login-trust")) {
      const trust = document.createElement("div"); trust.className = "qorg-login-trust"; trust.textContent = config.login_trust_message; body.append(trust);
    }
    if (config.login_show_security_footer && !card.querySelector(".qorg-login-security")) {
      const security = document.createElement("div"); security.className = "qorg-login-security"; security.textContent = __("Secure session protected by your organization settings."); card.append(security);
    }
    if (config.login_focus_first_field) setTimeout(() => card.querySelector('input:not([type="hidden"]):not([disabled])')?.focus(), 80);
  }

  async function addLanguagePicker(config) {
    if (!config.show_login_language_switcher || document.querySelector("[data-qorg-guest-language],.language-selector,[data-language-selector]")) return;
    const host = document.querySelector(".for-login .page-card"); if (!host) return;
    const response = await frappe.call("qorg.qorg.design_system.api.get_available_languages");
    const rows = response.message || []; if (!rows.length) return;
    const wrap = document.createElement("label"); wrap.className = "qorg-guest-language"; wrap.dataset.qorgGuestLanguage = "1";
    const label = document.createElement("span"); label.textContent = __("Language");
    const select = document.createElement("select"); select.setAttribute("aria-label", __("Language"));
    rows.forEach((row) => { const option = document.createElement("option"); option.value = row.name; option.textContent = row.language_name || row.name; option.selected = row.name === (frappe.boot?.lang || frappe.lang); select.append(option); });
    select.addEventListener("change", () => { const url = new URL(location.href); url.searchParams.set("lang", select.value); location.href = url.toString(); });
    wrap.append(label, select); host.append(wrap);
  }

  function enhanceWebForm(config) {
    const form = document.querySelector(".web-form, .web-form-container"); if (!form) return;
    form.dataset.qorgEnhanced = "1";
    if (config.public_validation_summary && !form.querySelector(".qorg-validation-summary")) {
      const summary = document.createElement("div"); summary.className = "qorg-validation-summary"; summary.hidden = true; summary.setAttribute("role", "alert"); summary.setAttribute("aria-live", "polite"); form.prepend(summary);
      form.addEventListener("invalid", () => { const invalid = [...form.querySelectorAll(":invalid")]; if (!invalid.length) return; summary.hidden = false; summary.textContent = __("Review the highlighted fields before continuing."); }, true);
      form.addEventListener("input", () => { if (!form.querySelector(":invalid")) summary.hidden = true; });
    }
  }

  async function initialize() {
    try {
      const response = await frappe.call("qorg.qorg.design_system.api.get_effective_configuration");
      const config = response.message || {};
      if (!config.enabled) return;
      applyVariables(config); applyPublicAttributes(config);
      if (config.apply_to_login) { buildLogin(config); await addLanguagePicker(config); }
      if (config.apply_to_qorg_web_components) enhanceWebForm(config);
    } catch (error) { console.warn("QOrg public experience restored Frappe Standard.", error); }
  }
  onReady(initialize);
})();
