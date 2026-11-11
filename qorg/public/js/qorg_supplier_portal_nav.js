(() => {
    "use strict";

    const PATHS = new Set(["/supplier-registration", "/tender-submission"]);
    const ITEMS = [
        ["Opportunities", "/procurement", "opportunities", "briefcase"],
        ["Supplier Profile", "/supplier-profile", "profile", "building"],
        ["My Bids", "/my-bids", "bids", "file"],
        ["Clarifications", "/my-clarifications", "clarifications", "message"],
        ["Contracts", "/my-contracts", "contracts", "contract"],
    ];

    function basePath() {
        for (const path of PATHS) {
            if (location.pathname === path || location.pathname.startsWith(`${path}/`)) return path;
        }
        return null;
    }

    function activeKey(path) {
        return path === "/supplier-registration" ? "profile" : "bids";
    }

    function mount() {
        const path = basePath();
        if (!path || document.querySelector(".qorg-supplier-nav[data-qorg-injected='1']")) return true;
        const container = document.querySelector(".web-form-container, .web-form-wrapper, main .container");
        if (!container) return false;

        const nav = document.createElement("nav");
        nav.className = "qorg-supplier-nav";
        nav.dataset.qorgInjected = "1";
        nav.setAttribute("aria-label", "Supplier portal navigation");
        const brand = document.createElement("div");
        brand.className = "qorg-supplier-nav__brand";
        const brandMark = document.createElement("span");
        brandMark.className = "qorg-supplier-nav__brand-mark";
        brandMark.textContent = "Q";
        const brandLabel = document.createElement("span");
        brandLabel.textContent = typeof window.__ === "function" ? window.__("Supplier Portal") : "Supplier Portal";
        brand.append(brandMark, brandLabel);
        nav.appendChild(brand);

        const inner = document.createElement("div");
        inner.className = "qorg-supplier-nav__inner";
        const active = activeKey(path);

        ITEMS.forEach(([label, href, key, iconName]) => {
            const link = document.createElement("a");
            link.className = `qorg-supplier-nav__link${key === active ? " is-active" : ""}`;
            link.href = href;
            const icon = document.createElement("span");
            icon.className = `qorg-supplier-nav__icon qorg-supplier-nav__icon--${iconName}`;
            icon.setAttribute("aria-hidden", "true");
            const text = document.createElement("span");
            text.textContent = typeof window.__ === "function" ? window.__(label) : label;
            link.append(icon, text);
            if (key === active) link.setAttribute("aria-current", "page");
            inner.appendChild(link);
        });
        nav.appendChild(inner);
        container.prepend(nav);
        return true;
    }

    if (!mount()) {
        let attempts = 0;
        const timer = setInterval(() => {
            attempts += 1;
            if (mount() || attempts >= 80) clearInterval(timer);
        }, 50);
    }
    document.addEventListener("DOMContentLoaded", mount, {once: true});
})();
