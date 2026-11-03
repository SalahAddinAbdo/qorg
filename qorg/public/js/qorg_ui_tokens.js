(() => {
    "use strict";
    const root = document.documentElement;
    const cacheKey = "qorg-ui-tokens-v1.2.1";

    function resolveScope() {
        const path = window.location.pathname.replace(/\/+$/, "") || "/";
        return path === "/app" || path.startsWith("/app/") ||
            path === "/desk" || path.startsWith("/desk/")
            ? "desk"
            : "web";
    }

    // qorg_ui_tokens.js is the first Q Org runtime file in both app_include_js
    // and web_include_js. Correct the scope synchronously before any cached
    // tokens, theme requests, widgets, or route callbacks can paint.
    root.dataset.qorgScope = resolveScope();
    if (root.dataset.qorgScope === "desk") {
        root.dataset.qorgThemeMode = "desk";
    }

    function apply(tokens = {}) {
        const map = {
            "--primary-color": tokens.primary_color,
            "--brand-color": tokens.primary_color,
            "--qorg-secondary-color": tokens.secondary_color,
            // Compatibility aliases for Frappe components that still read the
            // framework-wide variables. The modern visible Q Org fields remain
            // the only runtime source of truth; hidden legacy values are ignored.
            "--bg-color": "var(--qorg-page-bg)",
            "--fg-color": "var(--qorg-surface-bg)",
            "--card-bg": "var(--qorg-surface-bg)",
            "--control-bg": "var(--qorg-control-bg)",
            "--text-color": "var(--qorg-text)",
            "--text-muted": "var(--qorg-muted-text)",
            "--border-color": "var(--qorg-border)",
            "--light-border-color": "var(--qorg-border)",
            "--border-radius": "var(--qorg-default-field-radius)",
            "--border-radius-lg": "var(--qorg-default-card-radius)",
            "--card-border-radius": "var(--qorg-default-card-radius)",
            "--font-size-xs": tokens.font_size_xs ? `${tokens.font_size_xs}px` : null,
            "--font-size-sm": tokens.font_size_sm ? `${tokens.font_size_sm}px` : null,
            "--font-size-base": tokens.font_size_base ? `${tokens.font_size_base}px` : null,
            "--font-size-lg": tokens.font_size_lg ? `${tokens.font_size_lg}px` : null,
            "--font-size-xl": tokens.font_size_h4 ? `${tokens.font_size_h4}px` : null,
            "--font-size-2xl": tokens.font_size_h3 ? `${tokens.font_size_h3}px` : null,
            "--font-size-3xl": tokens.font_size_h2 ? `${tokens.font_size_h2}px` : null,
            "--font-size-4xl": tokens.font_size_h1 ? `${tokens.font_size_h1}px` : null,
            "--font-size-6xl": tokens.font_size_display ? `${tokens.font_size_display}px` : null,
            "--qorg-font-family": tokens.font_family,
            "--qorg-body-line-height": tokens.body_line_height,
            "--qorg-paragraph-line-height": tokens.paragraph_line_height,
            "--qorg-heading-line-height": tokens.heading_line_height,
            "--qorg-font-weight-regular": tokens.font_weights?.[0],
            "--qorg-font-weight-medium": tokens.font_weights?.[Math.min(1, (tokens.font_weights?.length || 1) - 1)],
            "--qorg-font-weight-semibold": tokens.font_weights?.[Math.min(2, (tokens.font_weights?.length || 1) - 1)],
            "--qorg-font-weight-bold": tokens.font_weights?.[(tokens.font_weights?.length || 1) - 1],
        };
        Object.entries(map).forEach(([name, value]) => {
            if (value !== null && value !== undefined && value !== "") root.style.setProperty(name, value);
        });
        root.dataset.qorgTokens = "1";
        if (tokens.font_stylesheet_url && !document.querySelector("link[data-qorg-ui-font]")) {
            const link = document.createElement("link");
            link.rel = "stylesheet";
            link.href = tokens.font_stylesheet_url;
            link.dataset.qorgUiFont = "1";
            document.head.append(link);
        }
    }

    try { apply(JSON.parse(localStorage.getItem(cacheKey) || "null") || {}); } catch (_) {}

    const load = () => frappe.call({method: "qorg.qorg.design_system.api.get_ui_configuration", type: "GET"})
        .then((response) => {
            const tokens = response.message || {};
            localStorage.setItem(cacheKey, JSON.stringify(tokens));
            apply(tokens);
        });

    if (window.frappe?.after_ajax) frappe.after_ajax(load);
    else if (window.frappe?.call) load();
})();
