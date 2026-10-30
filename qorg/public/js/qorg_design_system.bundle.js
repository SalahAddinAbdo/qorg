(() => {
  "use strict";

  const state = {
    configuration: null,
    createMenu: null,
    languageMenu: null,
    dock: null,
    settingsPromise: null,
    createPromise: null,
    observer: null,
    routeTimer: null,
    reconcileToken: 0,
    installedVariables: new Set(),
    originalTheme: document.documentElement.getAttribute("data-theme"),
  };

  const ROOT_ATTRIBUTES = [
    "data-qorg-design-system",
    "data-qorg-experience",
    "data-qorg-density",
    "data-qorg-surface-hierarchy",
    "data-qorg-navigation-emphasis",
    "data-qorg-page-header",
    "data-qorg-section-presentation",
    "data-qorg-table-presentation",
    "data-qorg-section-headings",
    "data-qorg-compact-tables",
    "data-qorg-sticky-list",
    "data-qorg-reduced-motion",
    "data-qorg-focus",
    "data-qorg-rtl",
    "data-qorg-reduced-transparency",
    "data-qorg-form-controls",
    "data-qorg-toolbar",
    "data-qorg-grid",
    "data-qorg-alternate-views",
    "data-qorg-dialogs",
    "data-qorg-workflow-timeline",
    "data-qorg-states",
    "data-qorg-sticky-primary-columns",
    "data-qorg-numeric-alignment",
    "data-qorg-workspace-layout",
    "data-qorg-kpi-cards",
    "data-qorg-chart-presentation",
    "data-qorg-priority-panels",
    "data-qorg-activity-panels",
    "data-qorg-operational-tables",
    "data-qorg-workspace-quick-actions",
    "data-qorg-dashboard-reflow",
    "data-qorg-dashboard-reduced-motion",
    "data-qorg-control-height-policy",
    "data-qorg-small-text-height",
    "data-qorg-focus-ring-style",
    "data-qorg-page-width",
    "data-qorg-app-rail-style",
    "data-qorg-module-sidebar-style",
    "data-qorg-navbar-search-style",
    "data-qorg-breadcrumb-emphasis",
    "data-qorg-menu-density",
    "data-qorg-workspace-content-width",
    "data-qorg-workspace-grid-policy",
    "data-qorg-workspace-card-style",
    "data-qorg-workspace-card-height",
    "data-qorg-workspace-heading-accent",
    "data-qorg-nested-surfaces",
    "data-qorg-section-actions",
    "data-qorg-mixed-bidi",
  ];

  const normalizeKey = (value, fallback = "default") =>
    String(value || fallback)
      .trim()
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-|-$/g, "");

  function clearAppearance() {
    const root = document.documentElement;
    ROOT_ATTRIBUTES.forEach((name) => root.removeAttribute(name));
    state.installedVariables.forEach((name) => root.style.removeProperty(name));
    state.installedVariables.clear();
    if (state.originalTheme) root.setAttribute("data-theme", state.originalTheme);
    else root.removeAttribute("data-theme");
  }

  function applyAppearance(configuration, preview = false) {
    clearAppearance();
    if ((!configuration?.enabled || !configuration?.apply_to_desk) && !preview) return;

    const root = document.documentElement;
    root.dataset.qorgDesignSystem = preview ? "preview" : "active";
    root.dataset.qorgExperience = normalizeKey(configuration.experience_style, "q-org-executive");
    root.dataset.qorgDensity = normalizeKey(configuration.density, "comfortable");
    root.dataset.qorgSurfaceHierarchy = normalizeKey(configuration.surface_hierarchy, "layered");
    root.dataset.qorgNavigationEmphasis = normalizeKey(configuration.navigation_emphasis, "balanced");
    root.dataset.qorgPageHeader = normalizeKey(configuration.page_header_style, "executive");
    root.dataset.qorgSectionPresentation = normalizeKey(configuration.section_presentation, "structured");
    root.dataset.qorgTablePresentation = normalizeKey(configuration.table_presentation, "enterprise");
    root.dataset.qorgSectionHeadings = configuration.enhanced_section_headings ? "1" : "0";
    root.dataset.qorgCompactTables = configuration.compact_child_tables ? "1" : "0";
    root.dataset.qorgStickyList = configuration.sticky_list_header ? "1" : "0";
    root.dataset.qorgReducedMotion = configuration.respect_reduced_motion ? "1" : "0";
    root.dataset.qorgFocus = configuration.enhanced_focus_visibility ? "1" : "0";
    root.dataset.qorgRtl = configuration.rtl_spacing_corrections ? "1" : "0";
    root.dataset.qorgReducedTransparency = configuration.reduced_transparency ? "1" : "0";
    root.dataset.qorgFormControls = normalizeKey(configuration.form_control_style, "enterprise");
    root.dataset.qorgToolbar = normalizeKey(configuration.toolbar_style, "unified");
    root.dataset.qorgGrid = normalizeKey(configuration.grid_style, "enterprise");
    root.dataset.qorgAlternateViews = normalizeKey(configuration.alternate_view_style, "enterprise");
    root.dataset.qorgDialogs = normalizeKey(configuration.dialog_style, "enterprise");
    root.dataset.qorgWorkflowTimeline = normalizeKey(configuration.workflow_timeline_style, "enterprise");
    root.dataset.qorgStates = normalizeKey(configuration.state_presentation, "illustrated-minimal");
    root.dataset.qorgStickyPrimaryColumns = configuration.sticky_primary_columns ? "1" : "0";
    root.dataset.qorgNumericAlignment = configuration.numeric_alignment ? "1" : "0";
    root.dataset.qorgWorkspaceLayout = normalizeKey(configuration.workspace_layout_style, "enterprise-canvas");
    root.dataset.qorgKpiCards = normalizeKey(configuration.kpi_card_style, "executive");
    root.dataset.qorgChartPresentation = normalizeKey(configuration.chart_presentation, "balanced");
    root.dataset.qorgPriorityPanels = normalizeKey(configuration.priority_panel_style, "action-oriented");
    root.dataset.qorgActivityPanels = normalizeKey(configuration.activity_panel_style, "timeline-cards");
    root.dataset.qorgOperationalTables = normalizeKey(configuration.operational_table_style, "enterprise");
    root.dataset.qorgWorkspaceQuickActions = configuration.workspace_quick_actions ? "1" : "0";
    root.dataset.qorgDashboardReflow = configuration.dashboard_responsive_reflow ? "1" : "0";
    root.dataset.qorgDashboardReducedMotion = configuration.dashboard_reduce_decorative_motion ? "1" : "0";
    root.dataset.qorgControlHeightPolicy = normalizeKey(configuration.control_height_policy, "enterprise-best");
    root.dataset.qorgSmallTextHeight = normalizeKey(configuration.small_text_height_policy, "comfortable");
    root.dataset.qorgFocusRingStyle = normalizeKey(configuration.focus_ring_style, "outline-and-soft-glow");
    root.dataset.qorgPageWidth = normalizeKey(configuration.page_width_policy, "wide-adaptive");
    root.dataset.qorgAppRailStyle = normalizeKey(configuration.app_rail_style, "integrated-executive");
    root.dataset.qorgModuleSidebarStyle = normalizeKey(configuration.module_sidebar_style, "integrated-executive");
    root.dataset.qorgNavbarSearchStyle = normalizeKey(configuration.navbar_search_style, "subtle-brand");
    root.dataset.qorgBreadcrumbEmphasis = normalizeKey(configuration.breadcrumb_emphasis, "current-page");
    root.dataset.qorgMenuDensity = normalizeKey(configuration.menu_density, "comfortable");
    root.dataset.qorgWorkspaceContentWidth = normalizeKey(configuration.workspace_content_width, "wide-adaptive");
    root.dataset.qorgWorkspaceGridPolicy = normalizeKey(configuration.workspace_grid_policy, "adaptive");
    root.dataset.qorgWorkspaceCardStyle = normalizeKey(configuration.workspace_card_style, "executive-subtle");
    root.dataset.qorgWorkspaceCardHeight = normalizeKey(configuration.workspace_card_height_policy, "content-based");
    root.dataset.qorgWorkspaceHeadingAccent = normalizeKey(configuration.workspace_heading_accent, "short-underline");
    root.dataset.qorgNestedSurfaces = normalizeKey(configuration.nested_surface_policy, "avoid-nested-cards");
    root.dataset.qorgSectionActions = normalizeKey(configuration.section_action_style, "inline");
    root.dataset.qorgMixedBidi = configuration.mixed_content_bidi_safety ? "1" : "0";

    if (configuration.theme_mode_policy === "Dark" || configuration.experience_style === "QOrg Midnight") {
      root.setAttribute("data-theme", "dark");
    } else if (configuration.theme_mode_policy === "Light") {
      root.setAttribute("data-theme", "light");
    }

    Object.entries(configuration.css_variables || {}).forEach(([name, value]) => {
      if (!name.startsWith("--qorg-") || typeof value !== "string") return;
      root.style.setProperty(name, value);
      state.installedVariables.add(name);
    });
  }

  async function getConfiguration(force = false) {
    if (!force && state.settingsPromise) return state.settingsPromise;
    state.settingsPromise = frappe
      .call("qorg.qorg.design_system.api.get_effective_configuration")
      .then((response) => response.message || {})
      .catch((error) => {
        state.settingsPromise = null;
        throw error;
      });
    return state.settingsPromise;
  }

  async function loadAppearance(force = false) {
    if (!window.frappe || frappe.session?.user === "Guest") return;
    try {
      state.configuration = await getConfiguration(force);
      applyAppearance(state.configuration);
      await mountActionDock();
    } catch (error) {
      clearAppearance();
      console.warn("QOrg Enterprise Experience restored Frappe Standard.", error);
    }
  }

  function icon(name, size = "md") {
    try {
      return frappe.utils.icon(name, size);
    } catch (error) {
      return '<span aria-hidden="true">•</span>';
    }
  }

  function removeOverlay(name) {
    document.querySelector(`[data-qorg-overlay="${name}"]`)?.remove();
  }

  function closeOverlays() {
    removeOverlay("create");
    removeOverlay("language");
    document.querySelectorAll("[data-qorg-dock-action]").forEach((button) => {
      button.setAttribute("aria-expanded", "false");
    });
  }

  function positionOverlay(overlay, anchor) {
    document.body.append(overlay);
    const rect = anchor.getBoundingClientRect();
    const width = Math.min(390, Math.max(280, window.innerWidth - 24));
    overlay.style.width = `${width}px`;

    const sidebarPlacement = state.dock?.dataset.qorgDockPlacement === "sidebar";
    const rtl = document.documentElement.dir === "rtl";
    let left;
    let top;

    if (sidebarPlacement && window.innerWidth > 767) {
      left = rtl ? rect.left - width - 12 : rect.right + 12;
      top = Math.min(rect.top, window.innerHeight - overlay.offsetHeight - 12);
    } else {
      left = rtl ? Math.max(12, rect.right - width) : Math.min(rect.left, window.innerWidth - width - 12);
      top = Math.max(12, rect.top - overlay.offsetHeight - 12);
    }

    overlay.style.left = `${Math.max(12, Math.min(left, window.innerWidth - width - 12))}px`;
    overlay.style.top = `${Math.max(12, top)}px`;
  }

  async function getCreateConfiguration(force = false) {
    if (!force && state.createPromise) return state.createPromise;
    state.createPromise = frappe
      .call("qorg.qorg.design_system.api.get_quick_create_menu")
      .then((response) => response.message || { enabled: false, items: [] })
      .catch((error) => {
        state.createPromise = null;
        throw error;
      });
    return state.createPromise;
  }

  function createCommandItem(item) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "qorg-command-item";
    button.setAttribute("role", "menuitem");
    button.dataset.searchText = `${item.label || ""} ${item.doctype || ""} ${item.description || ""}`.toLowerCase();

    const iconBox = document.createElement("span");
    iconBox.className = "qorg-command-icon";
    iconBox.innerHTML = icon(item.icon || "add", "md");

    const copy = document.createElement("span");
    copy.className = "qorg-command-copy";
    const title = document.createElement("span");
    title.className = "qorg-command-title";
    title.textContent = item.label || item.doctype;
    copy.append(title);
    if (item.description) {
      const description = document.createElement("span");
      description.className = "qorg-command-description";
      description.textContent = item.description;
      copy.append(description);
    }

    button.append(iconBox, copy);
    if (item.favorite) {
      const star = document.createElement("span");
      star.className = "qorg-command-favorite";
      star.innerHTML = icon("star", "sm");
      star.setAttribute("aria-label", __("Favorite"));
      button.append(star);
    }

    button.addEventListener("click", () => {
      closeOverlays();
      frappe.new_doc(item.doctype);
    });
    return button;
  }

  function renderCreateItems(container, configuration, query = "") {
    container.replaceChildren();
    const normalized = query.trim().toLowerCase();
    const visible = (configuration.items || []).filter((item) => {
      if (!normalized) return true;
      return `${item.label} ${item.doctype} ${item.description || ""}`.toLowerCase().includes(normalized);
    });

    if (!visible.length) {
      const empty = document.createElement("div");
      empty.className = "qorg-command-empty";
      empty.innerHTML = `${icon("search", "md")}<span>${__("No available document type matches the search.")}</span>`;
      container.append(empty);
      return;
    }

    const grouped = configuration.grouped !== false;
    const groups = new Map();
    visible.forEach((item) => {
      const key = grouped ? item.group || __("Other") : "";
      if (!groups.has(key)) groups.set(key, []);
      groups.get(key).push(item);
    });

    groups.forEach((items, group) => {
      if (group) {
        const heading = document.createElement("div");
        heading.className = "qorg-command-group-title";
        heading.textContent = group;
        container.append(heading);
      }
      items.forEach((item) => container.append(createCommandItem(item)));
    });
  }

  async function openCreateMenu(anchor) {
    closeOverlays();
    anchor.setAttribute("aria-expanded", "true");
    const configuration = await getCreateConfiguration();
    const overlay = document.createElement("section");
    overlay.className = "qorg-command-menu";
    overlay.dataset.qorgOverlay = "create";
    overlay.setAttribute("role", "dialog");
    overlay.setAttribute("aria-label", configuration.label || __("Create"));

    const header = document.createElement("header");
    header.className = "qorg-command-header";
    const eyebrow = document.createElement("span");
    eyebrow.className = "qorg-command-eyebrow";
    eyebrow.textContent = __("Quick action");
    const title = document.createElement("strong");
    title.textContent = configuration.label || __("Create new");
    header.append(eyebrow, title);
    overlay.append(header);

    const body = document.createElement("div");
    body.className = "qorg-command-body";
    if (configuration.search !== false && (configuration.items || []).length > 6) {
      const searchWrap = document.createElement("label");
      searchWrap.className = "qorg-command-search";
      searchWrap.innerHTML = icon("search", "sm");
      const input = document.createElement("input");
      input.type = "search";
      input.placeholder = __("Search document types");
      input.setAttribute("aria-label", __("Search document types"));
      searchWrap.append(input);
      body.append(searchWrap);
      input.addEventListener("input", () => renderCreateItems(list, configuration, input.value));
      setTimeout(() => input.focus(), 0);
    }

    const list = document.createElement("div");
    list.className = "qorg-command-list";
    list.setAttribute("role", "menu");
    body.append(list);
    renderCreateItems(list, configuration);
    overlay.append(body);
    positionOverlay(overlay, anchor);
  }

  async function openLanguageMenu(anchor) {
    closeOverlays();
    anchor.setAttribute("aria-expanded", "true");
    const response = await frappe.call("qorg.qorg.design_system.api.get_available_languages");
    const languages = response.message || [];
    const overlay = document.createElement("section");
    overlay.className = "qorg-command-menu qorg-language-menu";
    overlay.dataset.qorgOverlay = "language";
    overlay.setAttribute("role", "dialog");
    overlay.setAttribute("aria-label", __("Change Language"));

    const header = document.createElement("header");
    header.className = "qorg-command-header";
    header.innerHTML = `<span class="qorg-command-eyebrow">${__("Interface")}</span><strong>${__("Choose language")}</strong>`;
    overlay.append(header);

    const list = document.createElement("div");
    list.className = "qorg-command-list";
    list.setAttribute("role", "menu");
    const current = frappe.boot?.lang || frappe.lang;
    languages.forEach((language) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "qorg-command-item qorg-language-item";
      button.setAttribute("role", "menuitemradio");
      button.setAttribute("aria-checked", language.name === current ? "true" : "false");
      const copy = document.createElement("span");
      copy.className = "qorg-command-copy";
      const title = document.createElement("span");
      title.className = "qorg-command-title";
      title.textContent = language.language_name || language.name;
      const code = document.createElement("span");
      code.className = "qorg-command-description";
      code.textContent = language.name;
      copy.append(title, code);
      button.append(copy);
      if (language.name === current) {
        const selected = document.createElement("span");
        selected.className = "qorg-language-selected";
        selected.innerHTML = icon("tick", "sm");
        button.append(selected);
      }
      button.addEventListener("click", async () => {
        await frappe.call({
          method: "qorg.qorg.design_system.api.set_current_user_language",
          type: "POST",
          args: { language: language.name },
          freeze: true,
        });
        window.location.reload();
      });
      list.append(button);
    });
    overlay.append(list);
    positionOverlay(overlay, anchor);
  }

  function dockButton(type, label, iconName, primary = false) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `qorg-dock-action${primary ? " is-primary" : ""}`;
    button.dataset.qorgDockAction = type;
    button.setAttribute("aria-label", label);
    button.setAttribute("aria-haspopup", "dialog");
    button.setAttribute("aria-expanded", "false");
    button.title = state.configuration?.action_dock_tooltips ? label : "";
    const iconBox = document.createElement("span");
    iconBox.className = "qorg-dock-action-icon";
    iconBox.innerHTML = icon(iconName, "md");
    const text = document.createElement("span");
    text.className = "qorg-dock-action-label";
    text.textContent = label;
    button.append(iconBox, text);
    return button;
  }

  function findSidebarFooter() {
    const aligned = window.QOrgNavigation?.resolveMountPoint?.();
    if (aligned?.adapter && aligned.adapter !== "floating" && aligned.host) {
      return { host: aligned.host, before: aligned.before || null, adapter: aligned.adapter, collapsed: Boolean(aligned.collapsed) };
    }
    const userBlock = document.querySelector(
      ".desk-sidebar .sidebar-user, .standard-sidebar .sidebar-user, .layout-side-section .sidebar-user, .desk-sidebar .user-profile, .standard-sidebar .user-profile"
    );
    if (userBlock?.parentElement) return { host: userBlock.parentElement, before: userBlock, adapter: "legacy-sidebar", collapsed: false };
    const sidebar = document.querySelector(".desk-sidebar, .standard-sidebar, .layout-side-section");
    if (sidebar) return { host: sidebar, before: null, adapter: "legacy-sidebar", collapsed: sidebar.classList.contains("collapsed") };
    return null;
  }

  function desiredDockPlacement() {
    const config = state.configuration || {};
    if (window.innerWidth <= 767) return "floating";
    if (config.action_dock_desktop_placement === "Floating Edge") return "floating";
    const sidebar = findSidebarFooter();
    if (config.action_dock_desktop_placement === "Sidebar Footer") return sidebar ? "sidebar" : "floating";
    return sidebar ? "sidebar" : "floating";
  }

  function actionDockSignature(config, placement, target) {
    return JSON.stringify({
      placement,
      adapter: target?.adapter || "floating",
      collapsed: Boolean(target?.collapsed),
      create: Boolean(config.show_create_action),
      language: Boolean(config.show_language_action),
      createLabel: config.quick_create_button_label || __("Create"),
      collapsedBehavior: config.action_dock_collapsed_behavior || "Expand on Hover",
      mobilePlacement: config.action_dock_mobile_placement || "Floating Orb",
      tooltips: Boolean(config.action_dock_tooltips),
    });
  }
  function removeDuplicateDocks(keep = null) {
    document.querySelectorAll("[data-qorg-action-dock]").forEach((dock) => {
      if (dock !== keep) dock.remove();
    });
  }
  function placeActionDock(dock, placement, target) {
    dock.dataset.qorgDockPlacement = placement;
    if (placement === "sidebar" && target?.host?.isConnected) {
      dock.dataset.qorgNavigationAdapter = target.adapter || "sidebar";
      dock.dataset.qorgNavigationCollapsed = target.collapsed ? "1" : "0";
      if (target.before?.isConnected && target.before.parentElement === target.host) {
        if (dock.parentElement !== target.host || dock.nextSibling !== target.before) {
          target.host.insertBefore(dock, target.before);
        }
      } else if (dock.parentElement !== target.host) {
        target.host.append(dock);
      }
      delete dock.dataset.qorgMobilePlacement;
      return;
    }
    dock.dataset.qorgNavigationAdapter = "floating";
    dock.dataset.qorgNavigationCollapsed = "0";
    dock.dataset.qorgMobilePlacement = normalizeKey(
      state.configuration?.action_dock_mobile_placement,
      "floating-orb"
    );
    if (dock.parentElement !== document.body) document.body.append(dock);
  }
  function buildActionDock(config) {
    const dock = document.createElement("div");
    dock.className = "qorg-action-dock";
    dock.dataset.qorgActionDock = "1";
    dock.dataset.qorgDockCollapsed = normalizeKey(
      config.action_dock_collapsed_behavior,
      "expand-on-hover"
    );
    dock.setAttribute("aria-label", __("QOrg quick actions"));
    if (config.show_create_action) {
      const create = dockButton(
        "create",
        config.quick_create_button_label || __("Create"),
        "add",
        true
      );
      create.addEventListener("click", () => {
        if (document.querySelector('[data-qorg-overlay="create"]')) closeOverlays();
        else openCreateMenu(create).catch((error) => {
          closeOverlays();
          frappe.msgprint(__("The Create menu could not be loaded."));
          console.error(error);
        });
      });
      dock.append(create);
    }
    if (config.show_language_action) {
      const language = dockButton("language", __("Language"), "language");
      language.addEventListener("click", () => {
        if (document.querySelector('[data-qorg-overlay="language"]')) closeOverlays();
        else openLanguageMenu(language).catch((error) => {
          closeOverlays();
          frappe.msgprint(__("The language menu could not be loaded."));
          console.error(error);
        });
      });
      dock.append(language);
    }
    return dock;
  }
  async function mountActionDock() {
    const token = ++state.reconcileToken;
    const config = state.configuration || {};
    closeOverlays();
    if (!config.enable_action_dock || frappe.session?.user === "Guest" ||
        (!config.show_create_action && !config.show_language_action)) {
      removeDuplicateDocks();
      state.dock = null;
      return;
    }
    const placement = desiredDockPlacement();
    const target = placement === "sidebar" ? findSidebarFooter() : null;
    if (token !== state.reconcileToken) return;
    const signature = actionDockSignature(config, placement, target);
    let dock = document.querySelector("[data-qorg-action-dock]");
    removeDuplicateDocks(dock);
    if (!dock || dock.dataset.qorgSignature !== signature) {
      dock?.remove();
      dock = buildActionDock(config);
      dock.dataset.qorgSignature = signature;
    }
    placeActionDock(dock, placement, target);
    state.dock = dock;
  }
  function scheduleRemount(reason = "dom") {
    clearTimeout(state.routeTimer);
    state.routeTimer = setTimeout(() => {
      mountActionDock().catch((error) => console.warn(
        `QOrg Action Dock reconciliation failed (${reason}).`,
        error
      ));
    }, 90);
  }

  document.addEventListener("click", (event) => {
    const overlay = event.target.closest?.("[data-qorg-overlay]");
    const action = event.target.closest?.("[data-qorg-dock-action]");
    if (!overlay && !action) closeOverlays();
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closeOverlays();
  });
  window.addEventListener("resize", () => {
    closeOverlays();
    mountActionDock();
  }, { passive: true });
  window.addEventListener("scroll", closeOverlays, { passive: true, capture: true });

  window.qorgDesignSystem = {
    apply: applyAppearance,
    preview: (configuration) => applyAppearance(configuration, true),
    clear: clearAppearance,
    reload: () => loadAppearance(true),
    refreshCreateMenu: () => {
      state.createPromise = null;
      closeOverlays();
    },
    remountActionDock: mountActionDock,
  };

  frappe.realtime?.on("qorg_design_system_changed", () => {
    state.settingsPromise = null;
    state.createPromise = null;
    loadAppearance(true);
  });
  window.addEventListener("qorg-design-system-updated", () => {
    state.settingsPromise = null;
    state.createPromise = null;
    state.createMenu = null;
    state.languageMenu = null;
    loadAppearance(true);
  });
  frappe.router?.on?.("change", () => {
    closeOverlays();
    scheduleRemount("route");
    setTimeout(() => scheduleRemount("route-settled"), 320);
  });
  window.addEventListener("qorg:navigation-context-change", () => {
    closeOverlays();
    scheduleRemount("navigation-context");
  });

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => loadAppearance(), { once: true });
  } else {
    loadAppearance();
  }

  state.observer = new MutationObserver(() => scheduleRemount("mutation"));
  state.observer.observe(document.body, {
    childList: true,
    subtree: true,
    attributes: true,
    attributeFilter: ["class", "data-collapsed", "aria-expanded", "aria-current"],
  });
})();
