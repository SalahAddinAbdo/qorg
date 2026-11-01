(() => {
    "use strict";

    const AUTH_SELECTOR = ".for-login, .for-forgot, .for-signup, .for-email-login";
    const HASHES = new Set(["#login", "#forgot", "#signup", "#login-with-email-link"]);

    function getShell() {
        return document.querySelector(".qorg-login-shell");
    }

    function getFormHost(shell) {
        return shell?.querySelector(".qorg-login-form-host, .qorg-login-form-panel");
    }

    function getDirection() {
        const htmlDirection = document.documentElement.getAttribute("dir");
        const bodyDirection = document.body?.getAttribute("dir");
        const computedDirection = document.body ? getComputedStyle(document.body).direction : "ltr";
        const language = (document.documentElement.lang || "").toLowerCase();
        return htmlDirection || bodyDirection || (language.startsWith("ar") ? "rtl" : computedDirection) || "ltr";
    }

    function applyDirection(shell) {
        const direction = getDirection() === "rtl" ? "rtl" : "ltr";
        shell.dataset.qorgDirection = direction;
        shell.setAttribute("dir", direction);
    }

    function moveAuthSections(shell) {
        const host = getFormHost(shell);
        if (!host) return;

        document.querySelectorAll(AUTH_SELECTOR).forEach((section) => {
            if (!host.contains(section)) host.append(section);
        });
    }

    function normalizeAuthLinks(root = document) {
        root.querySelectorAll('a[href^="#"]').forEach((link) => {
            const hash = new URL(link.href, window.location.href).hash;
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
        const hash = new URL(link.href, window.location.href).hash;
        if (!HASHES.has(hash)) return;

        event.preventDefault();
        link.removeAttribute("target");
        if (window.location.hash === hash) window.dispatchEvent(new HashChangeEvent("hashchange"));
        else window.location.hash = hash;
        queueMicrotask(repair);
    }, true);

    window.addEventListener("hashchange", () => requestAnimationFrame(repair));
    window.addEventListener("pageshow", repair);
    document.addEventListener("DOMContentLoaded", repair, {once: true});

    if (!repair()) {
        let attempts = 0;
        const timer = window.setInterval(() => {
            attempts += 1;
            if (repair() || attempts >= 20) window.clearInterval(timer);
        }, 50);
    }
})();
