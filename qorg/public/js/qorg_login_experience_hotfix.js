(() => {
    "use strict";

    const AUTH_SELECTOR = ".for-login, .for-forgot, .for-signup, .for-email-login, .for-login-with-email-link, .for-reset-password";
    const HASHES = new Set(["#login", "#forgot", "#signup", "#login-with-email-link", "#reset-password"]);

    function direction() {
        const html = document.documentElement;
        const declared = html.getAttribute("dir") || document.body?.getAttribute("dir");
        if (declared === "rtl" || declared === "ltr") return declared;
        const language = (html.lang || document.body?.lang || "").toLowerCase();
        return /^(ar|fa|he|ur)(-|$)/.test(language) ? "rtl" : "ltr";
    }

    function shell() {
        return document.querySelector(".qorg-login-shell");
    }

    function formHost(loginShell) {
        return loginShell?.querySelector(".qorg-login-form-host") || loginShell?.querySelector(".qorg-login-form-panel");
    }

    function applyDirection(loginShell) {
        const value = direction();
        loginShell.dataset.qorgDirection = value;
        loginShell.setAttribute("dir", "ltr");
        loginShell.querySelector(".qorg-login-form-panel")?.setAttribute("dir", value);
        loginShell.querySelector(".qorg-login-visual")?.setAttribute("dir", value);
    }

    function moveAuthenticationSections(loginShell) {
        const host = formHost(loginShell);
        if (!host) return;
        document.querySelectorAll(AUTH_SELECTOR).forEach((section) => {
            if (!host.contains(section)) host.append(section);
            section.setAttribute("dir", loginShell.dataset.qorgDirection || direction());
        });
    }

    function normalizeLinks(root = document) {
        root.querySelectorAll('a[href^="#"]').forEach((link) => {
            const hash = new URL(link.href, location.href).hash;
            if (!HASHES.has(hash)) return;
            link.removeAttribute("target");
            link.removeAttribute("rel");
        });
    }

    function repair() {
        const loginShell = shell();
        if (!loginShell) return false;
        applyDirection(loginShell);
        moveAuthenticationSections(loginShell);
        normalizeLinks(loginShell);
        document.documentElement.dataset.qorgLoginReady = "1";
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
            if (repair() || attempts >= 40) clearInterval(timer);
        }, 25);
    }
})();
