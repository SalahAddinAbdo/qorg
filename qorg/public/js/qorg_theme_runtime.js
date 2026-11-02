(() => {
    "use strict";
    const CACHE_KEY = "qorg-theme-runtime-v1.3";
    const root = document.documentElement;

    const kebab = (value) => value.replaceAll("_", "-");
    const px = (value) => `${Math.max(0, Number(value) || 0)}px`;

    function declaration(entries, prefix) {
        return Object.entries(entries || {})
            .filter(([key]) => key.startsWith(prefix))
            .map(([key, value]) => `--qorg-${kebab(key.slice(prefix.length))}:${value}`)
            .join(";");
    }

    function sizeDeclarations(sizes) {
        return Object.entries(sizes || {}).map(([key, value]) => `--qorg-${kebab(key)}:${px(value)}`).join(";");
    }

    function assignWidgetPalettes() {
        ["number-widget-box", "shortcut-widget-box"].forEach((className) => {
            document.querySelectorAll(`.widget.${className}`).forEach((widget, index) => {
                widget.dataset.qorgPalette = String((index % 4) + 1);
            });
        });
    }

    function render(config) {
        const theme = config?.theme;
        if (!theme) return;
        const colors = theme.colors || {};
        const sizes = theme.sizes || {};
        const style = document.getElementById("qorg-theme-runtime") || document.head.appendChild(Object.assign(document.createElement("style"), {id: "qorg-theme-runtime"}));
        const shared = `--qorg-brand-primary:${theme.primary_color};--qorg-brand-secondary:${theme.secondary_color};${sizeDeclarations(sizes)}`;
        const deskLight = declaration(colors, "desk_light_");
        const deskDark = declaration(colors, "desk_dark_");
        const navLight = declaration(colors, "light_");
        const navDark = declaration(colors, "dark_");
        const webLight = declaration(colors, "web_light_");
        const webDark = declaration(colors, "web_dark_");
        const scope = location.pathname.startsWith("/app") || !!window.frappe?.boot ? "desk" : "web";
        root.dataset.qorgScope = scope;
        style.textContent = `
:root{${shared}}
[data-qorg-scope="desk"]{${deskLight};${navLight}}
[data-qorg-scope="desk"][data-theme="light"]{${deskLight};${navLight}}
[data-qorg-scope="desk"][data-theme="dark"]{${deskDark};${navDark}}
[data-qorg-scope="web"]{${webLight}}
[data-qorg-scope="web"][data-theme="light"]{${webLight}}
[data-qorg-scope="web"][data-theme="dark"]{${webDark}}
@media (prefers-color-scheme: dark){
  [data-qorg-scope="desk"]:not([data-theme="light"]):not([data-theme="dark"]){${deskDark};${navDark}}
  [data-qorg-scope="web"]:not([data-theme="light"]):not([data-theme="dark"]){${webDark}}
}
`;
        root.dataset.qorgThemeRuntime = "1";
        requestAnimationFrame(assignWidgetPalettes);
        setTimeout(assignWidgetPalettes, 250);
    }

    try { render(JSON.parse(localStorage.getItem(CACHE_KEY) || "null")); } catch (_) {}
    const load = () => frappe.call({method: "qorg.qorg.design_system.api.get_ui_configuration"}).then((response) => {
        const config = response.message || {};
        localStorage.setItem(CACHE_KEY, JSON.stringify(config));
        render(config);
    });
    if (window.frappe?.after_ajax) frappe.after_ajax(load); else if (window.frappe?.call) load();
})();
