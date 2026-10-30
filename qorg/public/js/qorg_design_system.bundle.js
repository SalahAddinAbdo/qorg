(() => {
  "use strict";
  const appliedVariables = new Set();
  const originalTheme = document.documentElement.getAttribute("data-theme");
  const managedAttributes = ["data-qorg-design-system", "data-qorg-density", "data-qorg-theme-mode", "data-qorg-section-headings", "data-qorg-compact-tables", "data-qorg-sticky-list", "data-qorg-reduced-motion", "data-qorg-focus", "data-qorg-rtl", "data-qorg-reduced-transparency"];
  let quickCreateLoadPromise = null;

  function clearDesign() {
    for (const name of managedAttributes) document.documentElement.removeAttribute(name);
    if (originalTheme) document.documentElement.setAttribute("data-theme", originalTheme);
    else document.documentElement.removeAttribute("data-theme");
    for (const name of appliedVariables) document.documentElement.style.removeProperty(name);
    appliedVariables.clear();
  }

  function applyDesign(configuration, preview = false) {
    clearDesign();
    if (!configuration?.enabled && !preview) return;
    const root = document.documentElement;
    root.dataset.qorgDesignSystem = preview ? "preview" : "active";
    root.dataset.qorgDensity = configuration.density || "Frappe Default";
    root.dataset.qorgThemeMode = configuration.theme_mode_policy || "Follow Frappe/System";
    if (configuration.theme_mode_policy === "Dark") root.setAttribute("data-theme", "dark");
    if (configuration.theme_mode_policy === "Light") root.setAttribute("data-theme", "light");
    root.dataset.qorgSectionHeadings = configuration.enhanced_section_headings ? "1" : "0";
    root.dataset.qorgCompactTables = configuration.compact_child_tables ? "1" : "0";
    root.dataset.qorgStickyList = configuration.sticky_list_header ? "1" : "0";
    root.dataset.qorgReducedMotion = configuration.respect_reduced_motion ? "1" : "0";
    root.dataset.qorgFocus = configuration.enhanced_focus_visibility ? "1" : "0";
    root.dataset.qorgRtl = configuration.rtl_spacing_corrections ? "1" : "0";
    root.dataset.qorgReducedTransparency = configuration.reduced_transparency ? "1" : "0";
    for (const [name, value] of Object.entries(configuration.css_variables || {})) {
      if (!name.startsWith("--qorg-") || typeof value !== "string") continue;
      root.style.setProperty(name, value);
      appliedVariables.add(name);
    }
  }

  async function loadDesign() {
    if (!window.frappe || frappe.session?.user === "Guest") return;
    try {
      const response = await frappe.call("qorg.qorg.design_system.api.get_effective_configuration");
      const configuration = response.message || {};
      if (configuration.apply_to_desk) applyDesign(configuration);
      else clearDesign();
    } catch (error) {
      clearDesign();
      console.warn("Q Org Design System restored Frappe Standard.", error);
    }
  }

  async function languageDialog() {
    const response = await frappe.call("qorg.qorg.design_system.api.get_available_languages");
    const options = (response.message || []).map((row) => ({
      label: row.language_name || row.name,
      value: row.name,
    }));
    const dialog = new frappe.ui.Dialog({
      title: __("Change Language"),
      fields: [{
        fieldname: "language",
        fieldtype: "Autocomplete",
        label: __("Language"),
        options,
        reqd: 1,
      }],
      primary_action_label: __("Apply"),
      primary_action: async (values) => {
        await frappe.call({
          method: "qorg.qorg.design_system.api.set_current_user_language",
          type: "POST",
          args: { language: values.language },
          freeze: true,
        });
        dialog.hide();
        window.location.reload();
      },
    });
    dialog.show();
  }

  function closeCreateMenu() {
    const menu = document.querySelector("[data-qorg-create-menu]");
    const button = document.querySelector("[data-qorg-create-button]");
    menu?.remove();
    button?.setAttribute("aria-expanded", "false");
  }

  function newDocument(doctype) {
    closeCreateMenu();
    if (!doctype) return;
    frappe.new_doc(doctype);
  }

  function createMenuElement(configuration, button) {
    const menu = document.createElement("div");
    menu.className = "qorg-create-menu";
    menu.dataset.qorgCreateMenu = "1";
    menu.setAttribute("role", "menu");
    menu.setAttribute("aria-label", configuration.label || __("Create"));

    const list = document.createElement("div");
    list.className = "qorg-create-menu-list";
    for (const item of configuration.items || []) {
      const action = document.createElement("button");
      action.type = "button";
      action.className = "qorg-create-menu-item";
      action.setAttribute("role", "menuitem");
      action.dataset.doctype = item.doctype;

      const icon = document.createElement("span");
      icon.className = "qorg-create-menu-icon";
      icon.setAttribute("aria-hidden", "true");
      try {
        icon.innerHTML = frappe.utils.icon(item.icon || "add", "md");
      } catch (error) {
        icon.textContent = "+";
      }

      const label = document.createElement("span");
      label.className = "qorg-create-menu-label";
      label.textContent = item.label || item.doctype;
      action.append(icon, label);
      action.addEventListener("click", () => newDocument(item.doctype));
      list.append(action);
    }

    if (!list.children.length) {
      const empty = document.createElement("div");
      empty.className = "qorg-create-menu-empty";
      empty.textContent = __("No document types are available for creation.");
      list.append(empty);
    }
    menu.append(list);
    document.body.append(menu);

    const rect = button.getBoundingClientRect();
    const menuWidth = Math.min(360, Math.max(260, window.innerWidth - 24));
    menu.style.width = `${menuWidth}px`;
    menu.style.top = `${Math.min(rect.bottom + 8, window.innerHeight - 100)}px`;
    const left = document.documentElement.dir === "rtl"
      ? Math.max(12, rect.right - menuWidth)
      : Math.min(window.innerWidth - menuWidth - 12, rect.left);
    menu.style.left = `${Math.max(12, left)}px`;

    const menuItems = [...menu.querySelectorAll("[role='menuitem']")];
    menuItems[0]?.focus();
    menu.addEventListener("keydown", (event) => {
      const current = menuItems.indexOf(document.activeElement);
      if (event.key === "Escape") {
        event.preventDefault();
        closeCreateMenu();
        button.focus();
      } else if (event.key === "ArrowDown" && menuItems.length) {
        event.preventDefault();
        menuItems[(current + 1 + menuItems.length) % menuItems.length].focus();
      } else if (event.key === "ArrowUp" && menuItems.length) {
        event.preventDefault();
        menuItems[(current - 1 + menuItems.length) % menuItems.length].focus();
      } else if (event.key === "Home") {
        event.preventDefault();
        menuItems[0]?.focus();
      } else if (event.key === "End") {
        event.preventDefault();
        menuItems.at(-1)?.focus();
      }
    });
    return menu;
  }

  async function toggleCreateMenu(button) {
    if (document.querySelector("[data-qorg-create-menu]")) {
      closeCreateMenu();
      return;
    }
    button.setAttribute("aria-expanded", "true");
    button.classList.add("is-loading");
    try {
      quickCreateLoadPromise ||= frappe.call("qorg.qorg.design_system.api.get_quick_create_menu");
      const response = await quickCreateLoadPromise;
      createMenuElement(response.message || {}, button);
    } catch (error) {
      quickCreateLoadPromise = null;
      button.setAttribute("aria-expanded", "false");
      frappe.msgprint(__("The Create menu could not be loaded."));
      console.error(error);
    } finally {
      button.classList.remove("is-loading");
    }
  }

  async function addTopbarControls() {
    if (frappe.session?.user === "Guest") return false;
    const navHosts = [...document.querySelectorAll(".navbar .navbar-nav, .desk-navbar .navbar-nav")];
    const host = navHosts.at(-1);
    if (!host) return false;

    if (!document.querySelector("[data-qorg-create-button]")) {
      try {
        const response = await frappe.call("qorg.qorg.design_system.api.get_quick_create_menu");
        const configuration = response.message || {};
        quickCreateLoadPromise = Promise.resolve(response);
        if (configuration.enabled) {
          const item = document.createElement("li");
          item.className = "nav-item qorg-create-nav-item";
          const button = document.createElement("button");
          button.type = "button";
          button.className = "btn btn-primary qorg-create-button";
          button.dataset.qorgCreateButton = "1";
          button.setAttribute("aria-haspopup", "menu");
          button.setAttribute("aria-expanded", "false");
          const plus = document.createElement("span");
          plus.className = "qorg-create-plus";
          plus.setAttribute("aria-hidden", "true");
          plus.textContent = "+";
          const label = document.createElement("span");
          label.textContent = configuration.label || __("Create");
          button.append(plus, label);
          button.addEventListener("click", () => toggleCreateMenu(button));
          item.append(button);
          host.prepend(item);
        }
      } catch (error) {
        console.warn("Q Org Create menu was not added.", error);
      }
    }

    if (!document.querySelector("[data-qorg-language-switcher]")) {
      const item = document.createElement("li");
      item.className = "nav-item";
      item.dataset.qorgLanguageSwitcher = "1";
      const button = document.createElement("button");
      button.type = "button";
      button.className = "btn-reset nav-link";
      button.setAttribute("aria-label", __("Change Language"));
      button.title = __("Change Language");
      button.innerHTML = '<span aria-hidden="true">文</span>';
      button.addEventListener("click", languageDialog);
      item.append(button);
      host.prepend(item);
    }
    return true;
  }

  function initializeTopbarControls() {
    addTopbarControls().then((ready) => {
      if (ready) return;
      const observer = new MutationObserver(async () => {
        if (await addTopbarControls()) observer.disconnect();
      });
      observer.observe(document.body, { childList: true, subtree: true });
      setTimeout(() => observer.disconnect(), 15000);
    });
  }

  document.addEventListener("click", (event) => {
    const menu = document.querySelector("[data-qorg-create-menu]");
    const button = document.querySelector("[data-qorg-create-button]");
    if (menu && !menu.contains(event.target) && !button?.contains(event.target)) closeCreateMenu();
  });
  window.addEventListener("resize", closeCreateMenu, { passive: true });
  window.addEventListener("scroll", closeCreateMenu, { passive: true, capture: true });

  window.qorgDesignSystem = {
    apply: applyDesign,
    preview: (configuration) => applyDesign(configuration, true),
    clear: clearDesign,
    reload: loadDesign,
    languageDialog,
    refreshCreateMenu: () => {
      quickCreateLoadPromise = null;
      closeCreateMenu();
      document.querySelector("[data-qorg-create-button]")?.closest("li")?.remove();
      addTopbarControls();
    },
  };

  frappe.realtime?.on("qorg_design_system_changed", () => {
    quickCreateLoadPromise = null;
    closeCreateMenu();
    document.querySelector("[data-qorg-create-button]")?.closest("li")?.remove();
    loadDesign();
    addTopbarControls();
  });
  initializeTopbarControls();
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", loadDesign, { once: true });
  else loadDesign();
})();
