(() => {
    "use strict";

    const AUTH_SELECTOR = ".for-login, .for-forgot, .for-signup, .for-email-login, .for-login-with-email-link, .for-reset-password";
    const HASHES = new Set(["#login", "#forgot", "#signup", "#login-with-email-link", "#reset-password"]);
    const AUTH_PATHS = new Set(["/", "/login", "/update-password", "/forgot", "/set-password"]);
    let repairQueued = false;
    let observer = null;


    const HASH_SECTION = {
        "#login": ".for-login",
        "#forgot": ".for-forgot",
        "#signup": ".for-signup",
        "#login-with-email-link": ".for-login-with-email-link, .for-email-login",
        "#reset-password": ".for-reset-password",
    };

    function activeAuthenticationSelector() {
        if (location.pathname === "/update-password" || location.pathname === "/set-password") {
            return ".for-reset-password";
        }
        return HASH_SECTION[location.hash] || ".for-login";
    }

    function revealActiveAuthenticationSection(loginShell) {
        const host = formHost(loginShell);
        if (!host) return false;
        const selector = activeAuthenticationSelector();
        let active = host.querySelector(selector);
        if (!active && selector !== ".for-login") active = host.querySelector(".for-login");
        host.querySelectorAll(AUTH_SELECTOR).forEach((section) => {
            const show = section === active;
            section.hidden = !show;
            section.setAttribute("aria-hidden", show ? "false" : "true");
            section.style.setProperty("display", show ? "block" : "none", "important");
            section.style.setProperty("visibility", show ? "visible" : "hidden", "important");
            section.style.setProperty("opacity", show ? "1" : "0", "important");
        });
        const panel = loginShell.querySelector(".qorg-login-form-panel");
        if (panel) {
            panel.hidden = false;
            panel.style.setProperty("display", "flex", "important");
            panel.style.setProperty("visibility", "visible", "important");
            panel.style.setProperty("opacity", "1", "important");
        }
        host.hidden = false;
        host.style.setProperty("display", "block", "important");
        host.style.setProperty("visibility", "visible", "important");
        host.style.setProperty("opacity", "1", "important");
        return !!active;
    }

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
        revealActiveAuthenticationSection(loginShell);
        normalizeLinks(loginShell);
        document.documentElement.dataset.qorgLoginReady = "1";
        return true;
    }

    function scheduleRepair() {
        if (repairQueued) return;
        repairQueued = true;
        requestAnimationFrame(() => {
            repair();
            // Frappe also changes authentication visibility during hash routing.
            // Re-apply once after its synchronous/hash handlers complete.
            window.setTimeout(repair, 40);
        });
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
