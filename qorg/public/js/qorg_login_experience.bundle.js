(() => {
    "use strict";

    const root = document.documentElement;
    const login = document.querySelector(".for-login, .login-content");
    if (!login || root.dataset.qorgLoginMounted === "1") return;

    root.dataset.qorgLoginMounted = "1";
    const cacheKey = "qorg-login-experience-v1.2";
    const fallback = {
        enable_login_experience: 1,
        login_image_panel_width: 48,
        login_slide_interval: 6,
        slides: [],
    };

    function safeJSON(value, fallbackValue) {
        try { return JSON.parse(value); } catch (_) { return fallbackValue; }
    }

    function applyTokens(tokens = {}) {
        const values = {
            "--primary-color": tokens.primary_color,
            "--brand-color": tokens.primary_color,
            "--qorg-secondary-color": tokens.secondary_color,
            "--bg-color": tokens.page_background_color,
            "--fg-color": tokens.surface_color,
            "--card-bg": tokens.surface_color,
            "--control-bg": tokens.control_background_color,
            "--text-color": tokens.primary_text_color,
            "--text-muted": tokens.muted_text_color,
            "--border-color": tokens.border_color,
            "--light-border-color": tokens.border_color,
            "--border-radius": Number.isFinite(+tokens.border_radius) ? `${tokens.border_radius}px` : null,
            "--border-radius-lg": Number.isFinite(+tokens.large_border_radius) ? `${tokens.large_border_radius}px` : null,
            "--card-border-radius": Number.isFinite(+tokens.large_border_radius) ? `${tokens.large_border_radius}px` : null,
            "--font-size-xs": tokens.font_size_xs ? `${tokens.font_size_xs}px` : null,
            "--font-size-sm": tokens.font_size_sm ? `${tokens.font_size_sm}px` : null,
            "--font-size-base": tokens.font_size_base ? `${tokens.font_size_base}px` : null,
            "--font-size-lg": tokens.font_size_lg ? `${tokens.font_size_lg}px` : null,
            "--font-size-xl": tokens.font_size_h4 ? `${tokens.font_size_h4}px` : null,
            "--font-size-2xl": tokens.font_size_h3 ? `${tokens.font_size_h3}px` : null,
            "--font-size-3xl": tokens.font_size_h2 ? `${tokens.font_size_h2}px` : null,
            "--font-size-4xl": tokens.font_size_h1 ? `${tokens.font_size_h1}px` : null,
            "--font-size-6xl": tokens.font_size_display ? `${tokens.font_size_display}px` : null,
            "--qorg-body-line-height": tokens.body_line_height,
            "--qorg-paragraph-line-height": tokens.paragraph_line_height,
            "--qorg-heading-line-height": tokens.heading_line_height,
            "--qorg-font-family": tokens.font_family,
        };
        Object.entries(values).forEach(([name, value]) => {
            if (value !== undefined && value !== null && value !== "") root.style.setProperty(name, value);
        });
    }

    function element(tag, className, text) {
        const node = document.createElement(tag);
        if (className) node.className = className;
        if (text) node.textContent = text;
        return node;
    }

    const originalParent = login.parentNode;
    const originalNextSibling = login.nextSibling;
    const shell = element("main", "qorg-login-shell");
    const visual = element("section", "qorg-login-visual");
    visual.setAttribute("aria-label", "Organization information");
    const visualHeader = element("div", "qorg-login-visual__header");
    const brand = element("div", "qorg-login-brand");
    const returnLink = element("a", "qorg-login-return", "Back to website");
    returnLink.href = "/";
    returnLink.append(element("span", "qorg-login-return__arrow", "→"));
    visualHeader.append(brand, returnLink);
    const slidesHost = element("div", "qorg-login-slides");
    const dots = element("div", "qorg-login-dots");
    dots.setAttribute("role", "tablist");
    visual.append(visualHeader, slidesHost, dots);

    const formPanel = element("section", "qorg-login-form-panel");
    const utility = element("div", "qorg-login-utility");
    const formHost = element("div", "qorg-login-form-host");
    shell.style.setProperty("--qorg-login-media-width", "48%");
    login.parentNode.insertBefore(shell, login);
    shell.append(visual, formPanel);
    formPanel.append(utility, formHost);
    formHost.append(login);

    let timer = null;
    let activeIndex = 0;
    let slideNodes = [];

    function setActive(index, focus = false) {
        if (!slideNodes.length) return;
        activeIndex = (index + slideNodes.length) % slideNodes.length;
        slideNodes.forEach((slide, i) => {
            const active = i === activeIndex;
            slide.classList.toggle("is-active", active);
            slide.setAttribute("aria-hidden", active ? "false" : "true");
        });
        dots.querySelectorAll("button").forEach((button, i) => {
            button.classList.toggle("is-active", i === activeIndex);
            button.setAttribute("aria-selected", i === activeIndex ? "true" : "false");
            if (focus && i === activeIndex) button.focus();
        });
    }

    function startTimer(seconds) {
        clearInterval(timer);
        if (slideNodes.length < 2 || matchMedia("(prefers-reduced-motion: reduce)").matches) return;
        timer = setInterval(() => setActive(activeIndex + 1), Math.max(3, Math.min(30, +seconds || 6)) * 1000);
    }

    function renderSlides(slides = [], seconds = 6) {
        slidesHost.replaceChildren();
        dots.replaceChildren();
        slideNodes = [];
        const items = slides.slice(0, 6);
        visual.classList.toggle("has-no-image", !items.length);
        items.forEach((item, index) => {
            const slide = element("article", "qorg-login-slide");
            slide.style.setProperty("--qorg-slide-image", `url(${JSON.stringify(String(item.image || ""))})`);
            if (item.mobile_image) slide.style.setProperty("--qorg-slide-mobile-image", `url(${JSON.stringify(String(item.mobile_image))})`);
            slide.style.setProperty("--qorg-slide-position", String(item.image_position || "Center").toLowerCase());
            slide.style.setProperty("--qorg-slide-overlay", String(Math.max(0, Math.min(100, +item.overlay_opacity || 38)) / 100));
            const copy = element("div", `qorg-login-slide__copy align-${String(item.text_alignment || "Center").toLowerCase()}`);
            if (item.title) copy.append(element("h2", "qorg-login-slide__title", item.title));
            if (item.subtitle) copy.append(element("p", "qorg-login-slide__subtitle", item.subtitle));
            slide.append(copy);
            if (index > 0) slide.setAttribute("aria-hidden", "true");
            slidesHost.append(slide);
            slideNodes.push(slide);

            const dot = element("button", "qorg-login-dot");
            dot.type = "button";
            dot.setAttribute("role", "tab");
            dot.setAttribute("aria-label", `Slide ${index + 1}`);
            dot.addEventListener("click", () => { setActive(index, true); startTimer(seconds); });
            dots.append(dot);
        });
        setActive(0);
        startTimer(seconds);
    }

    function loadFont(url) {
        if (!url || document.querySelector(`link[data-qorg-font="${CSS.escape(url)}"]`)) return;
        const link = document.createElement("link");
        link.rel = "stylesheet";
        link.href = url;
        link.dataset.qorgFont = url;
        document.head.append(link);
    }

    document.addEventListener("click", () => {
        const options = utility.querySelector(".qorg-language-options");
        const trigger = utility.querySelector(".qorg-language-trigger");
        if (options) options.hidden = true;
        if (trigger) trigger.setAttribute("aria-expanded", "false");
    });

    function renderLanguage(config) {
        utility.querySelector(".qorg-language-menu")?.remove();
        if (!config.show_login_language_switcher || !config.languages?.length) return;
        const menu = element("div", "qorg-language-menu");
        const trigger = element("button", "qorg-language-trigger");
        trigger.type = "button";
        trigger.setAttribute("aria-expanded", "false");
        const current = config.languages.find((item) => item.language_code === config.current_language) || config.languages[0];
        trigger.append(element("span", "qorg-language-icon", "◎"), element("span", "qorg-language-name", current.language_name), element("span", "qorg-language-chevron", "⌄"));
        const options = element("div", "qorg-language-options");
        options.hidden = true;
        config.languages.forEach((item) => {
            const button = element("button", "qorg-language-option", item.language_name);
            button.type = "button";
            button.dataset.language = item.language_code;
            button.addEventListener("click", async () => {
                await frappe.call({method: "qorg.qorg.design_system.api.set_login_language", args: {language: item.language_code}});
                location.reload();
            });
            options.append(button);
        });
        trigger.addEventListener("click", (event) => {
            event.stopPropagation();
            options.hidden = !options.hidden;
            trigger.setAttribute("aria-expanded", options.hidden ? "false" : "true");
        });
        menu.append(trigger, options);
        utility.append(menu);
    }

    function disableExperience() {
        clearInterval(timer);
        if (shell.isConnected) {
            if (originalNextSibling && originalNextSibling.parentNode === originalParent) originalParent.insertBefore(login, originalNextSibling);
            else originalParent.append(login);
            shell.remove();
        }
        delete root.dataset.qorgLoginExperience;
        delete root.dataset.qorgLoginMounted;
    }

    function render(config) {
        if (!config) return;
        if (config.enable_login_experience === 0) {
            disableExperience();
            return;
        }
        applyTokens(config.ui_tokens || {});
        loadFont(config.font_stylesheet_url);
        shell.style.setProperty("--qorg-login-media-width", `${Math.max(35, Math.min(60, +config.login_image_panel_width || 48))}%`);
        returnLink.firstChild.nodeValue = config.login_return_label || "Back to website";
        returnLink.href = config.login_return_url || "/";
        brand.replaceChildren();
        if (config.login_brand_logo) {
            const image = document.createElement("img");
            image.src = config.login_brand_logo;
            image.alt = "";
            brand.append(image);
        }
        renderSlides(config.slides || [], config.login_slide_interval);
        renderLanguage(config);
        formPanel.querySelector(".qorg-login-footer")?.remove();
        if (config.login_footer_text) formPanel.append(element("footer", "qorg-login-footer", config.login_footer_text));
        root.dataset.qorgLoginExperience = "1";
    }

    const cached = safeJSON(localStorage.getItem(cacheKey), null);
    render(cached || fallback);
    frappe.call({method: "qorg.qorg.design_system.api.get_login_experience"})
        .then((response) => {
            const config = response.message || fallback;
            localStorage.setItem(cacheKey, JSON.stringify(config));
            render(config);
        })
        .catch(() => render(cached || fallback));
})();
