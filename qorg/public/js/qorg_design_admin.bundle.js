(() => {
  "use strict";
  const SETTINGS = "Q Org Design System Settings";
  const esc = (value) => frappe.utils.escape_html(String(value ?? ""));
  const SECTION_DEFAULTS = {
    Core: ["theme_mode_policy","density","typography_policy","heading_weight","line_height_scale","control_radius","button_radius","card_radius","dialog_radius","border_strength","elevation_scale"],
    Colors: ["primary_accent","secondary_accent","neutral_accent","success_color","warning_color","danger_color","information_color","focus_color","navbar_surface","sidebar_surface","page_surface","card_surface","dialog_surface","input_surface","text_primary_color","text_muted_color","heading_color","border_color","selected_surface","hover_surface"],
    Controls: ["control_height_policy","custom_control_height","control_horizontal_padding","control_label_gap","small_text_height_policy","small_text_min_height","text_editor_min_height","select_option_height","focus_ring_style","form_control_style"],
    Shell: ["page_width_policy","page_max_width","page_inline_padding","app_rail_style","app_rail_icon_size","module_sidebar_style","module_sidebar_width","navigation_item_height","navbar_search_style","breadcrumb_emphasis","menu_density"],
    Navigation: ["navigation_emphasis","action_dock_desktop_placement","action_dock_mobile_placement","action_dock_collapsed_behavior","action_dock_tooltips","show_create_action","show_language_action"],
    Operational: ["form_control_style","toolbar_style","grid_style","alternate_view_style","dialog_style","workflow_timeline_style","state_presentation","sticky_primary_columns","numeric_alignment"],
    Workspace: ["workspace_layout_style","workspace_content_width","workspace_grid_policy","workspace_column_gap","workspace_row_gap","workspace_card_style","workspace_card_height_policy","workspace_heading_accent","nested_surface_policy","section_action_style","mixed_content_bidi_safety","kpi_card_style","chart_presentation","priority_panel_style","activity_panel_style","operational_table_style","workspace_quick_actions","dashboard_responsive_reflow","dashboard_reduce_decorative_motion"],
    Login: ["login_layout","login_experience_style","login_form_density","login_show_trust_message","login_trust_message","login_card_alignment","login_show_security_footer","login_focus_first_field"],
    Public: ["web_form_presentation","portal_presentation","public_card_style","public_validation_summary","public_success_presentation","public_mobile_sticky_actions"],
    Accessibility: ["contrast_policy","touch_target_policy","focus_visibility","reduced_motion","reduced_transparency"],
  };
  function currentForm() {
    return window.cur_frm?.doctype === SETTINGS ? window.cur_frm : null;
  }

  function previewMarkup(config, mode = "light", direction = "ltr", viewport = "desktop") {
    const values = { ...config };
    const smallTextHeight = values.small_text_height_policy === "Custom"
      ? Number(values.small_text_min_height || 88)
      : ({ Compact: 64, Comfortable: 88, Spacious: 120 }[values.small_text_height_policy] || 88);
    const controlHeight = values.control_height_policy === "Custom"
      ? Number(values.custom_control_height || 40)
      : ({ Compact: 34, Comfortable: 40, Spacious: 46, "Enterprise Best": 40 }[values.control_height_policy] || 40);
    const railIcon = Number(values.app_rail_icon_size || 20);
    const sideWidth = Math.max(96, Math.min(180, Math.round(Number(values.module_sidebar_width || 272) * 0.52)));
    const gap = Number(values.workspace_column_gap || 16);
    const rowGap = Number(values.workspace_row_gap || 16);
    return `<div class="qorg-admin-preview qorg-admin-preview-v28" data-mode="${esc(mode)}" dir="${esc(direction)}" data-viewport="${esc(viewport)}" style="--p:${esc(values.primary_accent || '#137690')};--s:${esc(values.secondary_accent || '#cbae66')};--bg:${esc(values.page_surface || '#f6f8fa')};--card:${esc(values.card_surface || '#fff')};--ink:${esc(values.text_primary_color || '#0f3246')};--muted:${esc(values.text_muted_color || '#606c77')};--line:${esc(values.border_color || '#d6e0e4')};--qap-control:${controlHeight}px;--qap-small:${smallTextHeight}px;--qap-rail-icon:${railIcon}px;--qap-side-width:${sideWidth}px;--qap-col-gap:${gap}px;--qap-row-gap:${rowGap}px;">
      <nav class="qap-rail" aria-label="App rail"><b>Q</b><button class="active">⌂</button><button>▦</button><button>✓</button><button>◎</button></nav>
      <aside class="qap-side"><strong>QOrg</strong><span class="active">Dashboard</span><span>Projects</span><span>Finance</span><span>People</span><div class="qap-actions"><button class="primary">＋ Create</button><button>文 Language</button></div></aside>
      <main class="qap-main"><header><div><small>Enterprise Workspace</small><h3>Operational overview</h3></div><div class="qap-search">⌕ Search</div></header>
      <section class="qap-kpis"><article><small>Active projects</small><b>24</b></article><article><small>Completion</small><b>78%</b></article><article><small>Pending actions</small><b>12</b></article></section>
      <section class="qap-heading"><h4>Performance and priority</h4><button>New action</button></section>
      <section class="qap-grid"><article class="qap-chart"><h4>Performance</h4><div class="bars"><i></i><i></i><i></i><i></i><i></i></div></article><article><h4>Priority</h4><p><span class="dot high"></span>3 critical actions</p><p><span class="dot"></span>9 due this week</p></article></section>
      <section class="qap-form"><label>Project name<input value="Water Access Program"></label><label>Status<select><option>Active</option></select></label><label class="qap-small-label">Summary<textarea>Arabic and English mixed content preview.</textarea></label><button>Save</button></section>
      <section class="qap-activity"><header><h4>Activity</h4><button>+ New Email</button></header><p>Timeline content follows one surface and one spacing system.</p></section>
      </main></div>`;
  }
  function showLivePreview(config) {
    const dialog = new frappe.ui.Dialog({ title: __("QOrg Live Preview"), size: "extra-large", fields: [
      {fieldname:"mode",fieldtype:"Select",label:__("Mode"),options:"Light\nDark",default:"Light",columns:2},
      {fieldname:"direction",fieldtype:"Select",label:__("Direction"),options:"LTR\nRTL",default:"LTR",columns:2},
      {fieldname:"viewport",fieldtype:"Select",label:__("Viewport"),options:"Desktop\nTablet\nMobile",default:"Desktop",columns:2},
      {fieldname:"preview",fieldtype:"HTML",label:__("Preview")},
    ]});
    const render = () => dialog.fields_dict.preview.$wrapper.html(previewMarkup(config, dialog.get_value("mode").toLowerCase(), dialog.get_value("direction").toLowerCase(), dialog.get_value("viewport").toLowerCase()));
    ["mode","direction","viewport"].forEach((field) => dialog.fields_dict[field].$input.on("change", render));
    dialog.show(); render();
  }

  async function showPresetGallery(frm) {
    const response = await frappe.call("qorg.qorg.design_system.api.get_preset_gallery");
    const presets = response.message || [];
    const cards = presets.map((row, index) => `<button type="button" class="qorg-preset-card" data-index="${index}"><div class="swatches">${(row.swatches || []).map((color) => `<i style="background:${esc(color)}"></i>`).join("")}</div><strong>${esc(row.preset_name || row.name)}</strong><small>${esc(row.description || '')}</small></button>`).join("");
    const dialog = new frappe.ui.Dialog({title:__("Preset Gallery"),size:"large",fields:[{fieldname:"gallery",fieldtype:"HTML"}]});
    dialog.fields_dict.gallery.$wrapper.html(`<div class="qorg-preset-gallery">${cards || `<p>${__("No enabled presets were found.")}</p>`}</div>`);
    dialog.fields_dict.gallery.$wrapper.on("click", ".qorg-preset-card", async function () {
      const preset = presets[Number(this.dataset.index)];
      Object.entries(preset.configuration || {}).forEach(([field, value]) => { if (frm.fields_dict[field]) frm.set_value(field, value); });
      if (frm.fields_dict.active_preset) await frm.set_value("active_preset", preset.name);
      dialog.hide(); frappe.show_alert({message:__("Preset loaded into the form. Review and Apply when ready."),indicator:"blue"});
    });
    dialog.show();
  }

  function showSectionReset(frm) {
    const sections = Object.keys(SECTION_DEFAULTS);
    const dialog = new frappe.ui.Dialog({title:__("Reset a Design Section"),fields:[{fieldname:"section",fieldtype:"Select",label:__("Section"),options:sections.join("\n"),reqd:1}],primary_action_label:__("Reset Section"),primary_action(values){
      const fields = SECTION_DEFAULTS[values.section] || [];
      fields.forEach((fieldname) => { const df = frm.fields_dict[fieldname]?.df; if (df) frm.set_value(fieldname, df.default ?? (df.fieldtype === "Check" ? 0 : "")); });
      dialog.hide(); frappe.show_alert({message:__("Section reset to managed defaults. Apply to publish the change."),indicator:"orange"});
    }}); dialog.show();
  }

  async function showVisualValidation(frm) {
    const response = await frappe.call({method:"qorg.qorg.design_system.api.validate_visual_configuration",type:"POST",args:{configuration:JSON.stringify(frm.doc)}});
    const findings = response.message?.findings || [];
    const content = findings.length ? findings.map((x) => `<div class="qorg-finding ${esc(x.severity.toLowerCase())}"><strong>${esc(x.severity)} · ${esc(x.area)}</strong><p>${esc(x.message)}</p></div>`).join("") : `<div class="qorg-finding valid"><strong>${__("Visual validation passed")}</strong><p>${__("No blocking visual configuration issues were detected.")}</p></div>`;
    frappe.msgprint({title:__("Visual Validation"),wide:true,message:content,indicator:response.message?.valid ? "green" : "red"});
  }

  async function showComparison(frm) {
    const current = (await frappe.call("qorg.qorg.design_system.api.get_effective_configuration")).message || {};
    const preview = (await frappe.call({method:"qorg.qorg.design_system.api.preview",type:"POST",args:{configuration:JSON.stringify(frm.doc)}})).message || {};
    const dialog = new frappe.ui.Dialog({title:__("Theme Comparison"),size:"extra-large",fields:[{fieldname:"comparison",fieldtype:"HTML"}]});
    dialog.fields_dict.comparison.$wrapper.html(`<div class="qorg-theme-comparison"><section><h4>${__("Current")}</h4>${previewMarkup(current)}</section><section><h4>${__("Preview")}</h4>${previewMarkup(preview)}</section></div>`); dialog.show();
  }

  async function refreshPublishedExperience() {
    window.dispatchEvent(new CustomEvent("qorg-design-system-updated", { detail: { source: "settings" } }));
    if (window.QOrgNavigation?.refresh) window.QOrgNavigation.refresh();
  }
  window.QOrgDesignAdmin = { showLivePreview, showPresetGallery, showSectionReset, showVisualValidation, showComparison, refreshPublishedExperience };

  frappe.ui.form.on(SETTINGS, { refresh(frm) {
    frm.add_custom_button(__("Live Preview"), () => showLivePreview(frm.doc), __("Administration UX"));
    frm.add_custom_button(__("Preset Gallery"), () => showPresetGallery(frm), __("Administration UX"));
    frm.add_custom_button(__("Reset Section"), () => showSectionReset(frm), __("Administration UX"));
    frm.add_custom_button(__("Visual Validation"), () => showVisualValidation(frm), __("Administration UX"));
    frm.add_custom_button(__("Theme Comparison"), () => showComparison(frm), __("Administration UX"));
  }});
})();
