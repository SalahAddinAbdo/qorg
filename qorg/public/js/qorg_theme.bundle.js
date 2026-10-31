(() => {
  "use strict";
  const root = document.documentElement;
  const state = { config: null, create: null, host: null };
  const call = (method, args = {}) => frappe.call({ method, args }).then(r => r.message || {});
  const key = value => String(value || "").trim().toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
  const esc = value => frappe.utils.escape_html(String(value || ""));

  function clearTheme() {
    ["qorgTheme", "qorgPreset", "qorgMode", "qorgDensity", "qorgNavigation", "qorgSurface", "qorgWidth", "qorgShell"].forEach(name => delete root.dataset[name]);
    [...root.style].filter(name => name.startsWith("--qorg-")).forEach(name => root.style.removeProperty(name));
    document.querySelectorAll("[data-qorg-global-actions]").forEach(node => node.remove());
    state.host = null;
  }

  function shellAdapter() {
    const candidates = [
      ["modern-sidebar-header", ".desk-sidebar .sidebar-header, .module-sidebar .sidebar-header, [data-sidebar] .sidebar-header"],
      ["modern-sidebar-footer", ".desk-sidebar .sidebar-footer, .module-sidebar .sidebar-footer, [data-sidebar] .sidebar-footer"],
      ["modern-dock", ".desk-dock .dock-actions, [data-dock] .dock-actions, .app-dock .dock-actions"],
      ["page-head", ".page-head .page-actions, .page-head .standard-actions"],
      ["legacy-navbar", ".navbar .navbar-nav"],
    ];
    for (const [name, selector] of candidates) {
      const host = document.querySelector(selector);
      if (host) return { name, host };
    }
    return null;
  }

  function button(label, icon, kind, handler) {
    const node = document.createElement("button");
    node.type = "button";
    node.className = `btn btn-sm qorg-shell-action qorg-shell-action--${kind}`;
    node.dataset.qorgAction = kind;
    node.setAttribute("aria-label", label);
    node.title = label;
    node.innerHTML = `<span class="qorg-shell-action__icon" aria-hidden="true">${frappe.utils.icon(icon, "sm")}</span><span class="qorg-shell-action__label">${esc(label)}</span>`;
    node.addEventListener("click", handler);
    return node;
  }

  function mountActions() {
    if (!state.config?.enabled) return;
    const adapter = shellAdapter();
    if (!adapter) return;
    const existing = document.querySelector("[data-qorg-global-actions]");
    if (existing && existing.parentElement === adapter.host) return;
    existing?.remove();
    const actions = document.createElement("div");
    actions.className = "qorg-shell-actions";
    actions.dataset.qorgGlobalActions = adapter.name;
    if (state.config.show_create_action) actions.append(button(__("New"), "add", "create", openCreate));
    if (state.config.show_language_action) actions.append(button(__("Language"), "globe", "language", openLanguage));
    adapter.host.append(actions);
    state.host = adapter.name;
    root.dataset.qorgShell = adapter.name;
  }

  function apply(config) {
    clearTheme();
    state.config = config;
    if (!config?.enabled) return;
    root.dataset.qorgTheme = "1";
    root.dataset.qorgPreset = key(config.active_preset);
    root.dataset.qorgMode = key(config.theme_mode);
    root.dataset.qorgDensity = key(config.density);
    root.dataset.qorgNavigation = key(config.navigation_style);
    root.dataset.qorgSurface = key(config.surface_style);
    root.dataset.qorgWidth = key(config.content_width);
    Object.entries(config.tokens || {}).forEach(([name, value]) => root.style.setProperty(name, String(value)));
    mountActions();
  }

  async function openCreate() {
    const data = state.create || (state.create = await call("qorg.qorg.design_system.api.get_quick_create_menu"));
    const dialog = new frappe.ui.Dialog({
      title: __("Create New"),
      size: "large",
      fields: [
        { fieldname: "search", fieldtype: "Data", label: __("Search document types") },
        { fieldname: "items", fieldtype: "HTML" },
      ],
    });
    const render = () => {
      const query = String(dialog.get_value("search") || "").trim().toLowerCase();
      const items = (data.items || []).filter(item => !query || `${item.label} ${item.group} ${item.description}`.toLowerCase().includes(query));
      const groups = items.reduce((result, item) => ((result[item.group] ||= []).push(item), result), {});
      const html = Object.entries(groups).map(([group, rows]) => `<section class="qorg-create-group"><h6>${esc(group)}</h6><div class="qorg-create-grid">${rows.map(item => `<button type="button" class="qorg-create-item" data-doctype="${esc(item.doctype)}"><span class="qorg-icon-tile qorg-icon-tile--brand">${frappe.utils.icon(item.icon || "add", "md")}</span><span><strong>${esc(item.label)}</strong>${item.description ? `<small>${esc(item.description)}</small>` : ""}</span></button>`).join("")}</div></section>`).join("") || `<p class="text-muted">${__("No available document types.")}</p>`;
      dialog.fields_dict.items.$wrapper.html(html).find("[data-doctype]").on("click", event => { dialog.hide(); frappe.new_doc(event.currentTarget.dataset.doctype); });
    };
    dialog.fields_dict.search.df.onchange = render;
    dialog.show();
    render();
  }

  async function openLanguage() {
    const data = await call("qorg.qorg.design_system.api.get_available_languages");
    const dialog = new frappe.ui.Dialog({
      title: __("Language"),
      fields: [{ fieldname: "language", fieldtype: "Select", label: __("Language"), options: (data.languages || []).map(item => ({ label: item.language_name, value: item.language_code })), default: data.current, reqd: 1 }],
      primary_action_label: __("Apply"),
      primary_action: async values => { await call("qorg.qorg.design_system.api.set_current_user_language", values); location.reload(); },
    });
    dialog.show();
  }

  async function load(force = 0) {
    try { apply(await call("qorg.qorg.design_system.api.get_effective_configuration", { force })); }
    catch (error) { console.warn("Q Org theme unavailable", error); }
  }

  function onRouteChange() { window.requestAnimationFrame(mountActions); }
  frappe.router?.on?.("change", onRouteChange);
  frappe.realtime?.on("qorg_theme_changed", () => load(1));
  window.addEventListener("resize", mountActions, { passive: true });
  window.qorgTheme = { apply, reload: () => load(1), clear: clearTheme };
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", () => load(), { once: true }); else load();
})();
