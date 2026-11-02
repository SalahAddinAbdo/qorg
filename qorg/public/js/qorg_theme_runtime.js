(() => {
    "use strict";

    const CACHE_KEY = "qorg-theme-runtime-v1.3";
    const root = document.documentElement;
    let paletteTimer = null;

    const kebab = (value) => value.replaceAll("_", "-");
    const px = (value) => `${Math.max(0, Number(value) || 0)}px`;

    function declaration(entries, prefix) {
        return Object.entries(entries || {})
            .filter(([key]) => key.startsWith(prefix))
            .map(([key, value]) => `--qorg-${kebab(key.slice(prefix.length))}:${value}`)
            .join(";");
    }

    function sizeDeclarations(sizes) {
        return Object.entries(sizes || {})
            .map(([key, value]) => `--qorg-${kebab(key)}:${px(value)}`)
            .join(";");
    }

    function assignPalette(selector) {
        document.querySelectorAll(selector).forEach((element, index) => {
            element.dataset.qorgPalette = String((index % 4) + 1);
        });
    }

    function assignWidgetPalettes() {
        assignPalette(".widget.number-widget-box, .number-card, .number-card-container .widget");
        assignPalette(".widget.shortcut-widget-box, .shortcut-widget-box, .shortcut-widget");
    }

    function scheduleWidgetPalettes() {
        clearTimeout(paletteTimer);
        requestAnimationFrame(assignWidgetPalettes);
        paletteTimer = setTimeout(assignWidgetPalettes, 180);
        setTimeout(assignWidgetPalettes, 650);
    }

    function render(config) {
        const theme = config?.theme;
        if (!theme) return;

        const colors = theme.colors || {};
        const sizes = theme.sizes || {};
        const style = document.getElementById("qorg-theme-runtime") || document.head.appendChild(
            Object.assign(document.createElement("style"), {id: "qorg-theme-runtime"})
        );
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
@media (prefers-color-scheme:dark){
 [data-qorg-scope="desk"]:not([data-theme="light"]):not([data-theme="dark"]){${deskDark};${navDark}}
 [data-qorg-scope="web"]:not([data-theme="light"]):not([data-theme="dark"]){${webDark}}
}`;
        root.dataset.qorgThemeRuntime = "1";
        scheduleWidgetPalettes();
    }



    function findQueryReportCheckArea(report) {
        const controls = (report.filters || [])
            .map((control) => control?.wrapper || control?.$wrapper?.get?.(0))
            .filter(Boolean);

        if (!controls.length) return null;

        const firstTop = controls[0].getBoundingClientRect().top;
        const nextRow = controls.find((element) => {
            const rect = element.getBoundingClientRect();
            return rect.height > 0 && rect.top > firstTop + 4;
        });

        return nextRow || controls.find((element) => getComputedStyle(element).display === "none") || null;
    }

    function installQueryReportCollapseCompatibility() {
        const prototype = window.frappe?.views?.QueryReport?.prototype;
        if (!prototype || prototype.__qorgCollapseCompatibility) return !!prototype;

        const original = prototype.toggle_filter_visiblity;
        if (typeof original !== "function") return false;

        prototype.toggle_filter_visiblity = function (...args) {
            if (!this.check_filter_area?.css) {
                const element = findQueryReportCheckArea(this);
                if (element && window.jQuery) this.check_filter_area = window.jQuery(element);
            }

            if (!this.check_filter_area?.css) {
                console.warn("Q Org: Query Report collapse area is unavailable; preserving report filters.");
                return;
            }

            return original.apply(this, args);
        };

        prototype.__qorgCollapseCompatibility = true;
        return true;
    }

    function scheduleQueryReportCompatibility() {
        let attempts = 0;
        const timer = window.setInterval(() => {
            attempts += 1;
            if (installQueryReportCollapseCompatibility() || attempts >= 40) {
                window.clearInterval(timer);
            }
        }, 50);
    }

    function load() {
        return frappe.call({method: "qorg.qorg.design_system.api.get_ui_configuration"}).then((response) => {
            const config = response.message || {};
            localStorage.setItem(CACHE_KEY, JSON.stringify(config));
            render(config);
        });
    }

    try { render(JSON.parse(localStorage.getItem(CACHE_KEY) || "null")); } catch (_) {}
    scheduleQueryReportCompatibility();

    if (window.frappe?.after_ajax) frappe.after_ajax(() => {
        load();
        scheduleWidgetPalettes();
        scheduleQueryReportCompatibility();
    });
    else if (window.frappe?.call) load();

    window.addEventListener("hashchange", scheduleWidgetPalettes);
    window.addEventListener("popstate", scheduleWidgetPalettes);
    window.addEventListener("pageshow", scheduleWidgetPalettes);
    document.addEventListener("click", () => setTimeout(scheduleWidgetPalettes, 80), true);

    if (window.frappe?.router?.on) {
        frappe.router.on("change", () => {
            scheduleWidgetPalettes();
            scheduleQueryReportCompatibility();
        });
    }
})();
