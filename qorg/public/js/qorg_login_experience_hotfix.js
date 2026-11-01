(() => {
    "use strict";

    const AUTH_SELECTOR = ".for-login, .for-forgot, .for-signup, .for-email-login";
    const HASHES = new Set(["#login", "#forgot", "#signup", "#login-with-email-link"]);

    function getDirection() {
        const html = document.documentElement;
        const language = (html.lang || document.body?.lang || "").toLowerCase();
        const declared = html.getAttribute("dir") || document.body?.getAttribute("dir");
        if (declared === "rtl" || declared === "ltr") return declared;
        if (/^(ar|fa|he|ur)(-|$)/.test(language)) return "rtl";
        return document.body && getComputedStyle(document.body).direction === "rtl" ? "rtl" : "ltr";
    }

    function getShell() {
        return document.querySelector(".qorg-login-shell");
    }

    function getFormHost(shell) {
        return shell?.querySelector(".qorg-login-form-host") || shell?.querySelector(".qorg-login-form-panel");
    }

    function applyDirection(shell) {
        const direction = getDirection();
        shell.dataset.qorgDirection = direction;
        shell.setAttribute("dir", "ltr");
        const panel = shell.querySelector(".qorg-login-form-panel");
        const visual = shell.querySelector(".qorg-login-visual");
        if (panel) panel.setAttribute("dir", direction);
        if (visual) visual.setAttribute("dir", direction);
    }

    function moveAuthSections(shell) {
        const host = getFormHost(shell);
        if (!host) return;
        document.querySelectorAll(AUTH_SELECTOR).forEach((section) => {
            if (!host.contains(section)) host.append(section);
            section.setAttribute("dir", shell.dataset.qorgDirection || getDirection());
        });
    }

    function normalizeAuthLinks(root = document) {
        root.querySelectorAll('a[href^="#"]').forEach((link) => {
            const hash = new URL(link.href, location.href).hash;
            if (!HASHES.has(hash)) return;
            link.removeAttribute("target");
            link.removeAttribute("rel");
        });
    }

    function repair() {
        const shell = getShell();
        if (!shell) return false;
        applyDirection(shell);
        moveAuthSections(shell);
        normalizeAuthLinks(shell);
        document.documentElement.dataset.qorgLoginHotfix = "1";
        return true;
    }

    document.addEventListener("click", (event) => {
        const link = event.target.closest('a[href^="#"]');
        if (!link) return;
        const hash = new URL(link.href, location.href).hash;
        if (!HASHES.has(hash)) return;
        event.preventDefault();
        link.removeAttribute("target");
        if (location.hash === hash) dispatchEvent(new HashChangeEvent("hashchange"));
        else location.hash = hash;
        requestAnimationFrame(repair);
    }, true);

    addEventListener("hashchange", () => requestAnimationFrame(repair));
    addEventListener("pageshow", repair);
    document.addEventListener("DOMContentLoaded", repair, {once: true});

    if (!repair()) {
        let attempts = 0;
        const timer = setInterval(() => {
            attempts += 1;
            if (repair() || attempts >= 20) clearInterval(timer);
        }, 50);
    }
})();
