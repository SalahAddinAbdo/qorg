(() => {
  "use strict";
  if (window.__qorgWebsiteV29) return;
  window.__qorgWebsiteV29 = true;
  const root = document.documentElement;
  const key = (value, fallback = "standard") => String(value || fallback).trim().toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
  const ready = (fn) => document.readyState === "loading" ? document.addEventListener("DOMContentLoaded", fn, { once: true }) : fn();
  const tr = (value) => typeof window.__ === "function" ? __(value) : value;

  function applyVariables(config) {
    if (config.font_source === "Managed Google Catalog" && !config.prefer_locally_hosted_fonts) {
      const families = [config.latin_font_family || "Inter", config.arabic_font_family || "Noto Sans Arabic"];
      const href = `https://fonts.googleapis.com/css2?${families.map((family) => `family=${encodeURIComponent(family).replace(/%20/g, "+")}:wght@400;500;600;700`).join("&")}&display=swap`;
      let link = document.querySelector("link[data-qorg-managed-fonts]");
      if (!link) { link = document.createElement("link"); link.rel = "stylesheet"; link.dataset.qorgManagedFonts = "1"; document.head.append(link); }
      link.href = href;
    }
    Object.entries(config.css_variables || {}).forEach(([name, value]) => {
      if (name.startsWith("--qorg-") && typeof value === "string") root.style.setProperty(name, value);
    });
    if (config.interface_font_stack) root.style.setProperty("--qorg-font-interface", config.interface_font_stack);
    if (config.arabic_font_stack) root.style.setProperty("--qorg-font-arabic", config.arabic_font_stack);
    if (config.latin_font_stack) root.style.setProperty("--qorg-font-latin", config.latin_font_stack);
  }
  function applyAttributes(config) {
    root.dataset.qorgWebForm = key(config.web_form_presentation, "enterprise");
    root.dataset.qorgPortal = key(config.portal_presentation, "enterprise");
    root.dataset.qorgPublicCards = key(config.public_card_style, "elevated");
    root.dataset.qorgLoginLayout = key(config.login_layout, "full-width-split");
    root.dataset.qorgLoginExperience = key(config.login_experience_style, "qorg-executive");
    root.dataset.qorgLoginDensity = key(config.login_form_density, "comfortable");
    root.dataset.qorgLoginMobile = key(config.login_mobile_visual_policy, "compact-header");
  }
  function translateManaged(value, fallback) {
    if (!value || value === fallback) return tr(fallback);
    return value;
  }
  function configureLogin(config) {
    const login = document.querySelector(".for-login");
    const card = login?.querySelector(".page-card");
    if (!login || !card || config.login_experience_style === "Frappe Standard") return;
    root.classList.add("qorg-login-enhanced");
    card.dataset.qorgLoginCard = "1";
    let visual = card.querySelector(".qorg-login-visual");
    if (!visual) {
      visual = document.createElement("aside");
      visual.className = "qorg-login-visual";
      visual.setAttribute("aria-label", tr("QOrg introduction"));
      visual.innerHTML = `<div class="qorg-login-visual-copy"><span class="qorg-login-brand">QOrg</span><h2></h2><p></p></div>`;
      card.append(visual);
    }
    if (config.login_visual_source === "Managed Image" && config.login_visual_image) {
      visual.style.backgroundImage = `linear-gradient(rgba(7,35,48,.2),rgba(7,35,48,.7)),url(${JSON.stringify(String(config.login_visual_image))})`;
      visual.dataset.visualSource = "image";
    } else {
      visual.style.removeProperty("background-image");
      visual.dataset.visualSource = "gradient";
      visual.dataset.gradient = key(config.login_visual_gradient, "qorg-blue");
    }
    visual.querySelector("h2").textContent = translateManaged(config.login_welcome_title, "Welcome to QOrg");
    visual.querySelector("p").textContent = translateManaged(config.login_welcome_subtitle, "Integrated, secure and efficient enterprise management.");

    const body = card.querySelector(".page-card-body");
    if (body) body.classList.add("qorg-login-form-panel");
    const heading = card.querySelector(".page-card-head");
    if (heading) heading.classList.add("qorg-login-form-head");
    if (config.login_show_trust_message && body && !body.querySelector(".qorg-login-trust")) {
      const trust = document.createElement("p");
      trust.className = "qorg-login-trust";
      trust.textContent = translateManaged(config.login_trust_message, "Secure access to your organization workspace.");
      body.append(trust);
    }
    if (config.login_show_security_footer && body && !body.querySelector(".qorg-login-security")) {
      const security = document.createElement("p");
      security.className = "qorg-login-security";
      security.textContent = tr("Secure session protected by your organization settings.");
      body.append(security);
    }
    if (config.login_focus_first_field && !window.matchMedia("(pointer: coarse)").matches) {
      requestAnimationFrame(() => card.querySelector('input:not([type="hidden"]):not([disabled])')?.focus({ preventScroll: true }));
    }
  }
  function setGuestLanguage(language) {
    const secure = location.protocol === "https:" ? "; Secure" : "";
    document.cookie = `preferred_language=${encodeURIComponent(language)}; Path=/; Max-Age=31536000; SameSite=Lax${secure}`;
    const url = new URL(location.href);
    url.searchParams.delete("lang");
    url.searchParams.set("_lang", language);
    location.assign(url.toString());
  }
  async function addLanguagePicker(config) {
    if (!config.show_login_language_switcher || document.querySelector("[data-qorg-guest-language]")) return;
    const host = document.querySelector(".for-login .page-card-body, .for-login .page-card");
    if (!host || !window.frappe?.call) return;
    const response = await frappe.call("qorg.qorg.design_system.api.get_available_languages");
    const rows = response.message || [];
    if (!rows.length) return;
    const wrap = document.createElement("label");
    wrap.className = "qorg-guest-language";
    wrap.dataset.qorgGuestLanguage = "1";
    const label = document.createElement("span"); label.textContent = tr("Language");
    const select = document.createElement("select"); select.setAttribute("aria-label", tr("Language"));
    const params = new URLSearchParams(location.search);
    const current = params.get("_lang") || document.documentElement.lang || frappe.boot?.lang || frappe.lang || "en";
    rows.forEach((row) => {
      const option = document.createElement("option");
      option.value = row.name;
      option.textContent = row.language_name || row.name;
      option.lang = row.name;
      option.selected = row.name === current;
      select.append(option);
    });
    select.addEventListener("change", () => setGuestLanguage(select.value));
    wrap.append(label, select);
    host.prepend(wrap);
  }
  function enhanceWebForm(config) {
    const form = document.querySelector(".web-form, .web-form-container");
    if (!form) return;
    form.dataset.qorgEnhanced = "1";
    if (config.public_validation_summary && !form.querySelector(".qorg-validation-summary")) {
      const summary = document.createElement("div");
      summary.className = "qorg-validation-summary";
      summary.hidden = true;
      summary.setAttribute("role", "alert");
      summary.setAttribute("aria-live", "polite");
      form.prepend(summary);
      form.addEventListener("invalid", () => {
        const invalid = [...form.querySelectorAll(":invalid")];
        if (!invalid.length) return;
        summary.hidden = false;
        summary.textContent = tr("Review the highlighted fields before continuing.");
      }, true);
      form.addEventListener("input", () => { if (!form.querySelector(":invalid")) summary.hidden = true; });
    }
  }
  async function initialize() {
    try {
      const response = await frappe.call("qorg.qorg.design_system.api.get_effective_configuration");
      const config = response.message || {};
      if (!config.enabled) return;
      applyVariables(config); applyAttributes(config);
      if (config.apply_to_login) { configureLogin(config); await addLanguagePicker(config); }
      if (config.apply_to_qorg_web_components) enhanceWebForm(config);
      root.dataset.qorgWebsiteReady = "1";
    } catch (error) {
      console.warn("QOrg website experience restored Frappe Standard.", error);
    }
  }
  ready(initialize);
})();
