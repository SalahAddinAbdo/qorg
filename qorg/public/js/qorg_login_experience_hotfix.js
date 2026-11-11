(() => {
    "use strict";

    const AUTH_SELECTOR = ".for-login, .for-forgot, .for-signup, .for-email-login, .for-login-with-email-link, .for-reset-password";
    const HASHES = new Set(["#login", "#forgot", "#signup", "#login-with-email-link", "#reset-password"]);
    const AUTH_PATHS = new Set(["/login", "/update-password", "/forgot", "/set-password"]);
    let repairQueued = false;
    let observer = null;

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

    function safeAppend(host, section) {
        if (!host || !section || host === section) return false;
        if (section.contains(host)) return false;
        if (section.parentElement === host) return false;
        host.appendChild(section);
        return true;
    }

    function moveAuthenticationSections(loginShell) {
        const host = formHost(loginShell);
        if (!host) return;
        document.querySelectorAll(AUTH_SELECTOR).forEach((section) => {
            safeAppend(host, section);
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
        repairQueued = false;
        if (!AUTH_PATHS.has(location.pathname)) return true;
        const loginShell = shell();
        if (!loginShell) return false;
        applyDirection(loginShell);
        moveAuthenticationSections(loginShell);
        normalizeLinks(loginShell);
        document.documentElement.dataset.qorgLoginReady = "1";
        return true;
    }

    function scheduleRepair() {
        if (repairQueued) return;
        repairQueued = true;
        requestAnimationFrame(repair);
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
        scheduleRepair();
    }, true);

    addEventListener("hashchange", scheduleRepair);
    addEventListener("pageshow", scheduleRepair);
    document.addEventListener("DOMContentLoaded", scheduleRepair, {once: true});

    if (AUTH_PATHS.has(location.pathname)) {
        observer = new MutationObserver(scheduleRepair);
        observer.observe(document.documentElement, {childList: true, subtree: true});
        let attempts = 0;
        const timer = setInterval(() => {
            attempts += 1;
            const done = repair();
            if (done || attempts >= 40) {
                clearInterval(timer);
                if (done && observer) {
                    setTimeout(() => observer.disconnect(), 1000);
                }
            }
        }, 25);
    }
})();
