(() => {
    "use strict";

    const ROOT_SELECTOR = 'html[data-qorg-scope="web"]';
    const SELECTOR = 'select.form-control:not([multiple]):not([size]), select.input-with-feedback:not([multiple]):not([size])';
    let counter = 0;

    function isDeskRoute() {
        const path = window.location.pathname.replace(/\/+$/, "") || "/";
        return path === "/app" || path.startsWith("/app/") ||
            path === "/desk" || path.startsWith("/desk/");
    }

    function isWeb() {
        return !isDeskRoute() && document.documentElement.matches(ROOT_SELECTOR);
    }

    function closeAll(except = null) {
        document.querySelectorAll('.qorg-web-select.is-open').forEach((wrapper) => {
            if (wrapper !== except) close(wrapper);
        });
    }

    function close(wrapper, restoreFocus = false) {
        const trigger = wrapper?.querySelector('.qorg-web-select__trigger');
        const list = wrapper?.querySelector('.qorg-web-select__list');
        if (!wrapper || !trigger || !list) return;
        wrapper.classList.remove('is-open');
        trigger.setAttribute('aria-expanded', 'false');
        list.hidden = true;
        list.querySelectorAll('[data-active="1"]').forEach((item) => delete item.dataset.active);
        if (restoreFocus) trigger.focus();
    }

    function open(wrapper) {
        const trigger = wrapper.querySelector('.qorg-web-select__trigger');
        const list = wrapper.querySelector('.qorg-web-select__list');
        if (trigger.disabled) return;
        closeAll(wrapper);
        wrapper.classList.add('is-open');
        trigger.setAttribute('aria-expanded', 'true');
        list.hidden = false;
        const selected = list.querySelector('[aria-selected="true"]') || list.querySelector('[role="option"]:not([aria-disabled="true"])');
        setActive(list, selected);
        selected?.scrollIntoView({block: 'nearest'});
    }

    function setActive(list, item) {
        list.querySelectorAll('[data-active="1"]').forEach((node) => delete node.dataset.active);
        if (!item || item.getAttribute('aria-disabled') === 'true') return;
        item.dataset.active = '1';
        list.setAttribute('aria-activedescendant', item.id);
    }

    function enabledItems(list) {
        return [...list.querySelectorAll('[role="option"]')].filter((item) => item.getAttribute('aria-disabled') !== 'true');
    }

    function moveActive(list, delta) {
        const items = enabledItems(list);
        if (!items.length) return;
        const current = list.querySelector('[data-active="1"]');
        let index = Math.max(0, items.indexOf(current));
        index = (index + delta + items.length) % items.length;
        setActive(list, items[index]);
        items[index].scrollIntoView({block: 'nearest'});
    }

    function choose(wrapper, item) {
        if (!item || item.getAttribute('aria-disabled') === 'true') return;
        const select = wrapper.querySelector('select');
        const index = Number(item.dataset.optionIndex);
        if (!select?.options[index]) return;
        select.selectedIndex = index;
        select.dispatchEvent(new Event('input', {bubbles: true}));
        select.dispatchEvent(new Event('change', {bubbles: true}));
        sync(wrapper);
        close(wrapper, true);
    }

    function sync(wrapper) {
        const select = wrapper.querySelector('select');
        const trigger = wrapper.querySelector('.qorg-web-select__trigger');
        const value = wrapper.querySelector('.qorg-web-select__value');
        const list = wrapper.querySelector('.qorg-web-select__list');
        if (!select || !trigger || !value || !list) return;
        const option = select.options[select.selectedIndex];
        value.textContent = option?.textContent?.trim() || select.getAttribute('placeholder') || '';
        trigger.disabled = select.disabled;
        trigger.setAttribute('aria-disabled', String(select.disabled));
        [...list.children].forEach((item) => {
            const selected = Number(item.dataset.optionIndex) === select.selectedIndex;
            item.setAttribute('aria-selected', String(selected));
        });
    }

    function buildOptions(select, list) {
        list.textContent = '';
        [...select.options].forEach((option, index) => {
            const item = document.createElement('li');
            item.id = `${list.id}-option-${index}`;
            item.className = 'qorg-web-select__option';
            item.setAttribute('role', 'option');
            item.setAttribute('aria-selected', String(index === select.selectedIndex));
            item.setAttribute('aria-disabled', String(option.disabled));
            item.dataset.optionIndex = String(index);

            const check = document.createElement('span');
            check.className = 'qorg-web-select__check';
            check.setAttribute('aria-hidden', 'true');
            check.textContent = '✓';

            const label = document.createElement('span');
            label.textContent = option.textContent.trim();
            item.append(check, label);
            item.addEventListener('pointermove', () => setActive(list, item));
            item.addEventListener('click', () => choose(item.closest('.qorg-web-select'), item));
            list.append(item);
        });
    }

    function enhance(select) {
        if (!isWeb() || select.dataset.qorgWebSelect === '1' || select.closest('.qorg-web-select')) return;
        if (select.multiple || Number(select.size || 0) > 1) return;

        const wrapper = document.createElement('div');
        wrapper.className = 'qorg-web-select';
        wrapper.dataset.qorgWebSelectWrapper = '1';
        select.parentNode.insertBefore(wrapper, select);
        wrapper.append(select);
        select.classList.add('qorg-web-select__native');
        select.dataset.qorgWebSelect = '1';

        const id = `qorg-web-select-${++counter}`;
        const trigger = document.createElement('button');
        trigger.type = 'button';
        trigger.className = 'qorg-web-select__trigger';
        trigger.setAttribute('aria-haspopup', 'listbox');
        trigger.setAttribute('aria-expanded', 'false');
        trigger.setAttribute('aria-controls', `${id}-list`);

        const value = document.createElement('span');
        value.className = 'qorg-web-select__value';
        const arrow = document.createElement('span');
        arrow.className = 'qorg-web-select__arrow';
        arrow.setAttribute('aria-hidden', 'true');
        trigger.append(value, arrow);

        const list = document.createElement('ul');
        list.id = `${id}-list`;
        list.className = 'qorg-web-select__list';
        list.setAttribute('role', 'listbox');
        list.tabIndex = -1;
        list.hidden = true;
        buildOptions(select, list);
        wrapper.append(trigger, list);

        trigger.addEventListener('click', () => wrapper.classList.contains('is-open') ? close(wrapper) : open(wrapper));
        trigger.addEventListener('keydown', (event) => {
            if (['ArrowDown', 'ArrowUp'].includes(event.key)) {
                event.preventDefault();
                if (!wrapper.classList.contains('is-open')) open(wrapper);
                else moveActive(list, event.key === 'ArrowDown' ? 1 : -1);
            } else if (event.key === 'Enter' || event.key === ' ') {
                event.preventDefault();
                if (!wrapper.classList.contains('is-open')) open(wrapper);
                else choose(wrapper, list.querySelector('[data-active="1"]'));
            } else if (event.key === 'Escape') {
                event.preventDefault();
                close(wrapper, true);
            } else if (event.key === 'Home' || event.key === 'End') {
                event.preventDefault();
                if (!wrapper.classList.contains('is-open')) open(wrapper);
                const items = enabledItems(list);
                setActive(list, event.key === 'Home' ? items[0] : items[items.length - 1]);
            }
        });

        select.addEventListener('change', () => sync(wrapper));
        new MutationObserver(() => {
            buildOptions(select, list);
            sync(wrapper);
        }).observe(select, {childList: true, subtree: true, attributes: true, attributeFilter: ['disabled', 'selected']});
        sync(wrapper);
    }

    function enhanceAll(root = document) {
        if (!isWeb()) return;
        if (root.matches?.(SELECTOR)) enhance(root);
        root.querySelectorAll?.(SELECTOR).forEach(enhance);
    }

    document.addEventListener('pointerdown', (event) => {
        if (!event.target.closest('.qorg-web-select')) closeAll();
    }, true);
    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') closeAll();
    });

    const start = () => {
        if (isDeskRoute()) return;

        enhanceAll();

        let scopeObserver = null;
        if (!isWeb()) {
            scopeObserver = new MutationObserver(() => {
                if (isDeskRoute()) {
                    scopeObserver.disconnect();
                    scopeObserver = null;
                    return;
                }
                if (!isWeb()) return;
                enhanceAll(document);
                scopeObserver.disconnect();
                scopeObserver = null;
            });
            scopeObserver.observe(document.documentElement, {
                attributes: true,
                attributeFilter: ['data-qorg-scope']
            });
        }

        new MutationObserver((records) => {
            if (isDeskRoute()) return;
            records.forEach((record) => record.addedNodes.forEach((node) => {
                if (node.nodeType === Node.ELEMENT_NODE) enhanceAll(node);
            }));
        }).observe(document.body, {childList: true, subtree: true});
    };

    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start, {once: true});
    else start();
})();
