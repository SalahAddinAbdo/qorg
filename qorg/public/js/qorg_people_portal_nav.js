(() => {
    "use strict";
    const ROUTES = new Map([["/external-profile-form", "profile"], ["/participation-application", "applications"]]);
    const ITEMS = [
        ["Opportunities", "/opportunities", "opportunities", "opportunities"],
        ["My Profile", "/external-profile-form", "profile", "profile"],
        ["My Applications", "/my-applications", "applications", "applications"],
    ];
    function matchRoute() {
        for (const [route, key] of ROUTES) {
            if (location.pathname === route || location.pathname.startsWith(`${route}/`)) return key;
        }
        return null;
    }
    function mount() {
        const active = matchRoute();
        if (!active || document.querySelector(".qorg-people-nav[data-qorg-injected='1']")) return !!active;
        const container = document.querySelector(".web-form-container, .web-form-wrapper, main .container");
        if (!container) return false;
        const nav = document.createElement("nav");
        nav.className = "qorg-people-nav";
        nav.dataset.qorgInjected = "1";
        nav.setAttribute("aria-label", "People and opportunities portal navigation");
        const brand = document.createElement("div");
        brand.className = "qorg-people-nav__brand";
        const mark = document.createElement("span"); mark.className = "qorg-people-nav__brand-mark"; mark.textContent = "Q";
        const label = document.createElement("span"); label.textContent = typeof window.__ === "function" ? window.__("People Portal") : "People Portal";
        brand.append(mark, label); nav.appendChild(brand);
        const inner = document.createElement("div"); inner.className = "qorg-people-nav__inner";
        ITEMS.forEach(([textValue, href, key, iconName]) => {
            const link = document.createElement("a");
            link.className = `qorg-people-nav__link${key === active ? " is-active" : ""}`;
            link.href = href;
            const icon = document.createElement("span"); icon.className = `qorg-people-nav__icon qorg-people-nav__icon--${iconName}`; icon.setAttribute("aria-hidden", "true");
            const text = document.createElement("span"); text.textContent = typeof window.__ === "function" ? window.__(textValue) : textValue;
            link.append(icon, text); if (key === active) link.setAttribute("aria-current", "page"); inner.appendChild(link);
        });
        nav.appendChild(inner); container.prepend(nav); return true;
    }
    if (!mount()) {
        let attempts = 0;
        const timer = setInterval(() => { attempts += 1; if (mount() || attempts >= 80) clearInterval(timer); }, 50);
    }
    document.addEventListener("DOMContentLoaded", mount, {once: true});
})();
