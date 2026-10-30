(() => {
  "use strict";

  const SELECTORS = {
    appsScreen: [
      '[data-page-route="apps"]', '.apps-page', '.apps-container', '.desktop-page',
      '[data-route="apps"]', '.app-grid', '.desktop-icons'
    ],
    dock: [
      '[data-testid="desk-dock"]', '[data-testid="dock"]', '[data-dock]',
      '.desk-dock', '.module-dock', '.app-dock', '.dock-container', '.dock'
    ],
    moduleSidebar: [
      '[data-testid="module-sidebar"]', '[data-module-sidebar]', '.module-sidebar',
      '.standard-sidebar', '.desk-sidebar', '.layout-side-section'
    ],
    sidebarFooter: [
      '[data-testid="module-sidebar-footer"]', '[data-sidebar-footer]',
      '.module-sidebar-footer', '.sidebar-footer', '.desk-sidebar-footer'
    ],
    userBlock: [
      '[data-testid="sidebar-user"]', '[data-sidebar-user]', '.sidebar-user',
      '.user-profile', '.sidebar-user-profile', '.user-area'
    ],
    mobileNavigation: [
      '[data-testid="mobile-navigation"]', '[data-mobile-sidebar]',
      '.mobile-sidebar', '.mobile-navigation', '.sidebar-overlay', '.offcanvas'
    ],
    appSwitcher: [
      '[data-testid="app-switcher"]', '[data-app-switcher]', '.app-switcher',
      '.app-selector', '.apps-dropdown'
    ],
    moduleItem: [
      '[data-module]', '[data-module-name]', '.module-item', '.dock-item',
      '.sidebar-item[data-route]'
    ],
    collapsed: [
      '[data-collapsed="true"]', '.collapsed', '.is-collapsed', '.sidebar-collapsed'
    ]
  };

  const state = {
    generation: 0,
    lastSignature: '',
    observer: null,
    settleTimer: null,
    listenersBound: false,
    nodeIds: new WeakMap(),
    nextNodeId: 1,
  };

  const unique = (items) => [...new Set(items.filter(Boolean))];
  function nodeIdentity(element) {
    if (!element) return null;
    if (!state.nodeIds.has(element)) state.nodeIds.set(element, state.nextNodeId++);
    return state.nodeIds.get(element);
  }
  const visible = (element) => Boolean(
    element && element.isConnected &&
    element.getClientRects().length &&
    getComputedStyle(element).visibility !== 'hidden' &&
    getComputedStyle(element).display !== 'none'
  );

  function queryAll(group, root = document) {
    return unique((SELECTORS[group] || []).flatMap((selector) => {
      try { return [...root.querySelectorAll(selector)]; }
      catch (error) { return []; }
    }));
  }

  function firstVisible(group, root = document) {
    return queryAll(group, root).find(visible) || null;
  }

  function closestAny(element, group) {
    if (!element?.closest) return null;
    for (const selector of SELECTORS[group] || []) {
      try {
        const result = element.closest(selector);
        if (result) return result;
      } catch (error) {}
    }
    return null;
  }

  function detectSidebar() {
    const mobile = firstVisible('mobileNavigation');
    if (mobile && window.innerWidth <= 991) {
      return { type: 'mobile', element: mobile };
    }
    const moduleSidebar = firstVisible('moduleSidebar');
    if (moduleSidebar) return { type: 'module-sidebar', element: moduleSidebar };
    return { type: 'none', element: null };
  }

  function detectDock() {
    const dock = firstVisible('dock');
    return dock ? { type: 'dock', element: dock } : { type: 'none', element: null };
  }

  function detectAppsScreen() {
    return firstVisible('appsScreen');
  }

  function isCollapsed(element) {
    if (!element) return false;
    if (element.getAttribute('aria-expanded') === 'false') return true;
    if (element.dataset.collapsed === 'true') return true;
    if (element.classList.contains('collapsed') || element.classList.contains('is-collapsed')) return true;
    return Boolean(firstVisible('collapsed', element));
  }

  function resolveMountPoint() {
    const sidebar = detectSidebar();
    const dock = detectDock();
    const rtl = document.documentElement.dir === 'rtl';

    if (sidebar.element) {
      const footer = firstVisible('sidebarFooter', sidebar.element);
      if (footer) {
        return { adapter: sidebar.type, host: footer, before: null, collapsed: isCollapsed(sidebar.element), rtl };
      }
      const user = firstVisible('userBlock', sidebar.element);
      if (user?.parentElement) {
        return { adapter: sidebar.type, host: user.parentElement, before: user, collapsed: isCollapsed(sidebar.element), rtl };
      }
      return { adapter: sidebar.type, host: sidebar.element, before: null, collapsed: isCollapsed(sidebar.element), rtl };
    }

    if (dock.element) {
      const user = firstVisible('userBlock', dock.element);
      return {
        adapter: 'dock',
        host: user?.parentElement || dock.element,
        before: user || null,
        collapsed: isCollapsed(dock.element),
        rtl,
      };
    }

    return { adapter: 'floating', host: document.body, before: null, collapsed: false, rtl };
  }

  function currentContext() {
    const sidebar = detectSidebar();
    const dock = detectDock();
    const route = window.frappe?.get_route?.() || [];
    const appSwitcher = firstVisible('appSwitcher');
    const activeModule = queryAll('moduleItem').find((item) =>
      item.matches('.active, .selected, [aria-current="page"], [data-active="true"]')
    );
    return {
      route,
      app: appSwitcher?.dataset?.app || appSwitcher?.textContent?.trim() || null,
      module: activeModule?.dataset?.module || activeModule?.dataset?.moduleName || activeModule?.textContent?.trim() || null,
      sidebar: sidebar.type,
      dock: dock.type,
      collapsed: isCollapsed(sidebar.element || dock.element),
      apps_screen: Boolean(detectAppsScreen()),
      mobile: window.innerWidth <= 991,
      rtl: document.documentElement.dir === 'rtl',
    };
  }

  function signature() {
    const context = currentContext();
    const mount = resolveMountPoint();
    return JSON.stringify({
      route: context.route,
      app: context.app,
      module: context.module,
      sidebar: context.sidebar,
      collapsed: context.collapsed,
      mobile: context.mobile,
      adapter: mount.adapter,
      hostId: nodeIdentity(mount.host),
      beforeId: nodeIdentity(mount.before),
      hostClass: mount.host?.className || '',
      dockId: nodeIdentity(detectDock().element),
      sidebarId: nodeIdentity(detectSidebar().element),
    });
  }

  function emitIfChanged(reason = 'dom') {
    const next = signature();
    if (next === state.lastSignature) return;
    state.lastSignature = next;
    state.generation += 1;
    window.dispatchEvent(new CustomEvent('qorg:navigation-context-change', {
      detail: { generation: state.generation, reason, context: currentContext(), mount: resolveMountPoint() },
    }));
  }

  function schedule(reason) {
    clearTimeout(state.settleTimer);
    state.settleTimer = setTimeout(() => emitIfChanged(reason), 90);
  }

  function selectorMatch(group) {
    return (SELECTORS[group] || []).map((selector) => {
      let elements = [];
      try { elements = [...document.querySelectorAll(selector)]; } catch (error) {}
      return {
        selector,
        count: elements.length,
        visible: elements.filter(visible).length,
        samples: elements.slice(0, 3).map((element) => ({
          tag: element.tagName,
          id: element.id || null,
          class: typeof element.className === 'string' ? element.className : null,
          role: element.getAttribute('role'),
          testid: element.getAttribute('data-testid'),
          aria_label: element.getAttribute('aria-label'),
        })),
      };
    }).filter((row) => row.count);
  }

  function audit() {
    const mount = resolveMountPoint();
    const report = {
      generated_on: new Date().toISOString(),
      href: location.href,
      user_agent: navigator.userAgent,
      viewport: { width: window.innerWidth, height: window.innerHeight, device_pixel_ratio: window.devicePixelRatio },
      direction: document.documentElement.dir || getComputedStyle(document.documentElement).direction,
      theme: document.documentElement.getAttribute('data-theme'),
      context: currentContext(),
      selected_adapter: mount.adapter,
      mount_point: mount.host ? {
        tag: mount.host.tagName,
        id: mount.host.id || null,
        class: typeof mount.host.className === 'string' ? mount.host.className : null,
        before_class: typeof mount.before?.className === 'string' ? mount.before.className : null,
      } : null,
      selector_matches: Object.fromEntries(Object.keys(SELECTORS).map((group) => [group, selectorMatch(group)])),
      qorg: {
        action_dock_count: document.querySelectorAll('[data-qorg-action-dock]').length,
        overlay_count: document.querySelectorAll('[data-qorg-overlay]').length,
        design_system_active: document.documentElement.hasAttribute('data-qorg-design-system'),
      },
    };
    return report;
  }

  async function copyAudit() {
    const payload = JSON.stringify(audit(), null, 2);
    if (navigator.clipboard?.writeText) await navigator.clipboard.writeText(payload);
    return payload;
  }

  function bind() {
    if (state.listenersBound) return;
    state.listenersBound = true;
    window.addEventListener('resize', () => schedule('resize'), { passive: true });
    window.addEventListener('popstate', () => schedule('popstate'));
    window.addEventListener('hashchange', () => schedule('hashchange'));
    window.frappe?.router?.on?.('change', () => schedule('route'));
    document.addEventListener('click', (event) => {
      if (closestAny(event.target, 'appSwitcher') || closestAny(event.target, 'moduleItem')) schedule('navigation-click');
    }, true);
    state.observer = new MutationObserver(() => schedule('mutation'));
    state.observer.observe(document.body, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ['class', 'data-collapsed', 'data-active', 'aria-expanded', 'aria-current'],
    });
    emitIfChanged('initial');
  }

  window.QOrgNavigation = {
    selectors: SELECTORS,
    visible,
    queryAll,
    detectSidebar,
    detectDock,
    detectAppsScreen,
    resolveMountPoint,
    currentContext,
    audit,
    copyAudit,
    refresh: () => emitIfChanged('manual'),
    bind,
  };

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', bind, { once: true });
  else bind();
})();
