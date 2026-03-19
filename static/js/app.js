/**
 * NavHCM Dashboard Application
 * Main JavaScript module for layout, theme management, sidebar, and utilities.
 *
 * This file handles:
 *  - Theme switching (light/dark)
 *  - Layout switching (vertical/horizontal/detached)
 *  - Sidebar size, color, and behavior
 *  - Topbar color
 *  - Layout width, position, direction
 *  - Preloader management
 *  - Theme customizer panel
 *  - CSRF-aware AJAX helpers for Django
 *  - Toast notifications, confirm dialogs, table search/filter
 */

(function () {
    "use strict";

    // =========================================================================
    // Constants
    // =========================================================================

    var STORAGE_KEY = "navhcm-theme-settings";

    var DEFAULTS = {
        theme: "light",
        layout: "vertical",
        sidebarSize: "default",
        sidebarColor: "dark",
        topbarColor: "light",
        layoutWidth: "fluid",
        layoutPosition: "fixed",
        direction: "ltr",
        preloader: false
    };

    var DATA_ATTRS = {
        theme: "data-theme",
        layout: "data-layout",
        sidebarSize: "data-sidebar-size",
        sidebarColor: "data-sidebar",
        topbarColor: "data-topbar",
        layoutWidth: "data-layout-width",
        layoutPosition: "data-layout-position",
        direction: "data-direction"
    };

    var MOBILE_BREAKPOINT = 992;
    var SUBMENU_ANIMATION_DURATION = 300;

    // =========================================================================
    // ThemeManager
    // =========================================================================

    /**
     * Manages all theme/layout settings. Reads and writes to localStorage,
     * applies data attributes to document.body, and provides toggle methods.
     */
    function ThemeManager() {
        this._settings = {};
        this._listeners = [];
        this._init();
    }

    /**
     * Load saved settings from localStorage, falling back to defaults.
     * Apply all settings to the DOM immediately.
     */
    ThemeManager.prototype._init = function () {
        var saved = this._loadFromStorage();
        var key;

        for (key in DEFAULTS) {
            if (DEFAULTS.hasOwnProperty(key)) {
                this._settings[key] = saved.hasOwnProperty(key)
                    ? saved[key]
                    : DEFAULTS[key];
            }
        }

        this._applyAll();
    };

    /**
     * Read the stored JSON blob. Returns an empty object on failure.
     */
    ThemeManager.prototype._loadFromStorage = function () {
        try {
            var raw = localStorage.getItem(STORAGE_KEY);
            if (raw) {
                return JSON.parse(raw);
            }
        } catch (e) {
            // Corrupted data -- fall through to defaults.
        }
        return {};
    };

    /**
     * Persist the current settings object to localStorage.
     */
    ThemeManager.prototype._saveToStorage = function () {
        try {
            localStorage.setItem(STORAGE_KEY, JSON.stringify(this._settings));
        } catch (e) {
            // Storage full or unavailable -- silently ignore.
        }
    };

    /**
     * Apply every setting as a data-attribute on document.body and
     * handle direction on the <html> element.
     */
    ThemeManager.prototype._applyAll = function () {
        var key;
        for (key in DATA_ATTRS) {
            if (DATA_ATTRS.hasOwnProperty(key)) {
                document.documentElement.setAttribute(DATA_ATTRS[key], this._settings[key]);
            }
        }

        // Direction is also reflected on <html> for CSS selectors.
        document.documentElement.setAttribute("dir", this._settings.direction);

        // Preloader visibility.
        this._applyPreloader();
    };

    /**
     * Apply a single setting: update internal state, DOM attribute, and storage.
     */
    ThemeManager.prototype._applySetting = function (key, value) {
        if (!DEFAULTS.hasOwnProperty(key)) {
            return;
        }

        this._settings[key] = value;

        if (DATA_ATTRS[key]) {
            document.documentElement.setAttribute(DATA_ATTRS[key], value);
        }

        if (key === "direction") {
            document.documentElement.setAttribute("dir", value);
        }

        if (key === "preloader") {
            this._applyPreloader();
        }

        this._saveToStorage();
        this._notifyListeners(key, value);
    };

    /**
     * Show or hide the preloader element based on current setting.
     */
    ThemeManager.prototype._applyPreloader = function () {
        var el = document.getElementById("preloader");
        if (!el) {
            return;
        }
        if (this._settings.preloader) {
            el.style.display = "";
            el.style.opacity = "1";
        } else {
            el.style.display = "none";
        }
    };

    /**
     * Notify all registered listeners of a setting change.
     */
    ThemeManager.prototype._notifyListeners = function (key, value) {
        for (var i = 0; i < this._listeners.length; i++) {
            try {
                this._listeners[i](key, value);
            } catch (e) {
                // Listener error should not break the chain.
            }
        }
    };

    // -- Public API -----------------------------------------------------------

    /**
     * Get the current value for a setting key.
     * @param {string} key - One of the keys from DEFAULTS.
     * @returns {*} The current value or undefined.
     */
    ThemeManager.prototype.get = function (key) {
        return this._settings[key];
    };

    /**
     * Get a shallow copy of all current settings.
     * @returns {Object}
     */
    ThemeManager.prototype.getAll = function () {
        var copy = {};
        var key;
        for (key in this._settings) {
            if (this._settings.hasOwnProperty(key)) {
                copy[key] = this._settings[key];
            }
        }
        return copy;
    };

    /**
     * Register a callback to be invoked on any setting change.
     * Callback signature: function(key, value).
     * @param {Function} fn
     */
    ThemeManager.prototype.onChange = function (fn) {
        if (typeof fn === "function") {
            this._listeners.push(fn);
        }
    };

    /**
     * Set the color theme.
     * @param {"light"|"dark"} value
     */
    ThemeManager.prototype.setTheme = function (value) {
        this._applySetting("theme", value);
    };

    /**
     * Toggle between light and dark theme.
     */
    ThemeManager.prototype.toggleTheme = function () {
        this.setTheme(this._settings.theme === "light" ? "dark" : "light");
    };

    /**
     * Set the layout mode.
     * @param {"vertical"|"horizontal"|"detached"} value
     */
    ThemeManager.prototype.setLayout = function (value) {
        this._applySetting("layout", value);
    };

    /**
     * Set the sidebar size.
     * @param {"default"|"compact"|"small"|"hover"} value
     */
    ThemeManager.prototype.setSidebarSize = function (value) {
        this._applySetting("sidebarSize", value);
    };

    /**
     * Set the sidebar color scheme.
     * @param {"light"|"dark"|"colored"} value
     */
    ThemeManager.prototype.setSidebarColor = function (value) {
        this._applySetting("sidebarColor", value);
    };

    /**
     * Set the topbar color scheme.
     * @param {"light"|"dark"} value
     */
    ThemeManager.prototype.setTopbarColor = function (value) {
        this._applySetting("topbarColor", value);
    };

    /**
     * Set the layout width.
     * @param {"fluid"|"boxed"} value
     */
    ThemeManager.prototype.setLayoutWidth = function (value) {
        this._applySetting("layoutWidth", value);
    };

    /**
     * Set the layout position (scrolling behavior of navbar/sidebar).
     * @param {"fixed"|"scrollable"} value
     */
    ThemeManager.prototype.setLayoutPosition = function (value) {
        this._applySetting("layoutPosition", value);
    };

    /**
     * Set the text direction.
     * @param {"ltr"|"rtl"} value
     */
    ThemeManager.prototype.setDirection = function (value) {
        this._applySetting("direction", value);
    };

    /**
     * Toggle between LTR and RTL.
     */
    ThemeManager.prototype.toggleDirection = function () {
        this.setDirection(this._settings.direction === "ltr" ? "rtl" : "ltr");
    };

    /**
     * Set whether the preloader should show.
     * @param {boolean} value
     */
    ThemeManager.prototype.setPreloader = function (value) {
        this._applySetting("preloader", !!value);
    };

    /**
     * Reset all settings to their default values.
     */
    ThemeManager.prototype.resetToDefaults = function () {
        var key;
        for (key in DEFAULTS) {
            if (DEFAULTS.hasOwnProperty(key)) {
                this._settings[key] = DEFAULTS[key];
            }
        }
        this._applyAll();
        this._saveToStorage();
        this._notifyListeners("*", null);
    };

    // =========================================================================
    // Sidebar
    // =========================================================================

    /**
     * Manages sidebar toggle, submenu expand/collapse, hover behavior,
     * active item highlighting, and mobile auto-collapse.
     *
     * @param {ThemeManager} themeManager
     */
    function Sidebar(themeManager) {
        this._tm = themeManager;
        this._sidebarEl = null;
        this._overlay = null;
        this._hoverExpanded = false;
        this._init();
    }

    /**
     * Locate DOM elements, bind events, highlight current menu item.
     */
    Sidebar.prototype._init = function () {
        this._sidebarEl = document.getElementById("app-sidebar") ||
                          document.querySelector(".app-menu") ||
                          document.querySelector(".navbar-menu") ||
                          document.querySelector(".app-sidebar") ||
                          document.querySelector(".vertical-menu");

        if (!this._sidebarEl) {
            return;
        }

        this._createOverlay();
        this._bindToggleButtons();
        this._bindSubmenus();
        this._bindMenuSections();
        this._bindHoverExpand();
        this._bindResize();
        this._highlightActiveItem();
        this._collapseInactiveSections();
        this._handleMobileInit();
    };

    /**
     * Create a backdrop overlay used when the sidebar is open on mobile.
     */
    Sidebar.prototype._createOverlay = function () {
        this._overlay = document.createElement("div");
        this._overlay.className = "sidebar-overlay";
        this._overlay.style.cssText =
            "position:fixed;top:0;left:0;width:100%;height:100%;z-index:1002;" +
            "background:rgba(0,0,0,0.4);display:none;transition:opacity .3s;opacity:0;";
        document.body.appendChild(this._overlay);

        var self = this;
        this._overlay.addEventListener("click", function () {
            self.close();
        });
    };

    /**
     * Bind click handlers on all elements that should toggle the sidebar.
     */
    Sidebar.prototype._bindToggleButtons = function () {
        var self = this;
        var togglers = document.querySelectorAll(
            '[data-toggle="sidebar"], .sidebar-toggle, .topnav-hamburger, #topnav-hamburger-icon, .hamburger-icon, #sidebar-toggle'
        );

        for (var i = 0; i < togglers.length; i++) {
            togglers[i].addEventListener("click", function (e) {
                e.preventDefault();
                self.toggle();
            });
        }
    };

    /**
     * Bind click events on sidebar menu items that have sub-menus.
     * Uses smooth height animation via max-height transitions.
     */
    Sidebar.prototype._bindSubmenus = function () {
        var menuLinks = this._sidebarEl.querySelectorAll(
            ".has-submenu > a, .has-sub > a, [data-toggle='submenu'], .menu-link[data-bs-toggle='collapse']"
        );

        for (var i = 0; i < menuLinks.length; i++) {
            menuLinks[i].addEventListener("click", this._onSubmenuClick.bind(this));
        }
    };

    /**
     * Handle a click on a parent menu item that owns a submenu.
     */
    Sidebar.prototype._onSubmenuClick = function (e) {
        e.preventDefault();

        var parentLi = e.currentTarget.parentElement;
        var submenu = parentLi.querySelector("ul, .sub-menu, .submenu, .collapse");
        if (!submenu) {
            return;
        }

        var isOpen = parentLi.classList.contains("open") ||
                     parentLi.classList.contains("mm-active");

        // Collapse siblings at the same level (accordion behavior).
        var siblings = parentLi.parentElement.children;
        for (var i = 0; i < siblings.length; i++) {
            if (siblings[i] !== parentLi) {
                this._collapseItem(siblings[i]);
            }
        }

        if (isOpen) {
            this._collapseItem(parentLi);
        } else {
            this._expandItem(parentLi, submenu);
        }
    };

    /**
     * Expand a submenu with a smooth slide-down animation.
     */
    Sidebar.prototype._expandItem = function (li, submenu) {
        li.classList.add("open", "mm-active");
        submenu.style.display = "block";
        submenu.style.overflow = "hidden";

        var fullHeight = submenu.scrollHeight;
        submenu.style.maxHeight = "0px";

        // Force reflow before starting the transition.
        void submenu.offsetHeight;

        submenu.style.transition = "max-height " + SUBMENU_ANIMATION_DURATION + "ms ease";
        submenu.style.maxHeight = fullHeight + "px";

        var cleanup = function () {
            submenu.style.maxHeight = "";
            submenu.style.overflow = "";
            submenu.style.transition = "";
            submenu.removeEventListener("transitionend", cleanup);
        };
        submenu.addEventListener("transitionend", cleanup);
    };

    /**
     * Collapse a menu item's submenu with a smooth slide-up animation.
     */
    Sidebar.prototype._collapseItem = function (li) {
        if (!li.classList.contains("open") && !li.classList.contains("mm-active")) {
            return;
        }

        var submenu = li.querySelector("ul, .sub-menu, .submenu, .collapse");
        if (!submenu) {
            li.classList.remove("open", "mm-active");
            return;
        }

        submenu.style.overflow = "hidden";
        submenu.style.maxHeight = submenu.scrollHeight + "px";

        // Force reflow.
        void submenu.offsetHeight;

        submenu.style.transition = "max-height " + SUBMENU_ANIMATION_DURATION + "ms ease";
        submenu.style.maxHeight = "0px";

        var done = function () {
            submenu.style.display = "none";
            submenu.style.maxHeight = "";
            submenu.style.overflow = "";
            submenu.style.transition = "";
            li.classList.remove("open", "mm-active");
            submenu.removeEventListener("transitionend", done);
        };
        submenu.addEventListener("transitionend", done);
    };

    // -- Menu Section (group-level) accordion --------------------------------

    /**
     * Bind click events on menu-title elements that act as section headers.
     */
    Sidebar.prototype._bindMenuSections = function () {
        var titles = this._sidebarEl.querySelectorAll('.menu-title[data-toggle="menu-section"]');
        var self = this;

        for (var i = 0; i < titles.length; i++) {
            titles[i].addEventListener("click", function (e) {
                e.preventDefault();
                var titleLi = this;
                var isCollapsed = titleLi.classList.contains("collapsed");

                // Accordion: collapse all other sections first.
                var allTitles = self._sidebarEl.querySelectorAll('.menu-title[data-toggle="menu-section"]');
                for (var j = 0; j < allTitles.length; j++) {
                    if (allTitles[j] !== titleLi) {
                        self._collapseSection(allTitles[j]);
                    }
                }

                if (isCollapsed) {
                    self._expandSection(titleLi);
                } else {
                    self._collapseSection(titleLi);
                }
            });
        }
    };

    /**
     * Get all nav-item siblings belonging to a menu-title section
     * (everything between this menu-title and the next one).
     */
    Sidebar.prototype._getSectionItems = function (menuTitleLi) {
        var items = [];
        var sibling = menuTitleLi.nextElementSibling;
        while (sibling && !sibling.classList.contains("menu-title")) {
            items.push(sibling);
            sibling = sibling.nextElementSibling;
        }
        return items;
    };

    /**
     * Collapse a section: hide its nav-items and mark title as collapsed.
     */
    Sidebar.prototype._collapseSection = function (menuTitleLi) {
        if (menuTitleLi.classList.contains("collapsed")) return;
        var items = this._getSectionItems(menuTitleLi);
        for (var i = 0; i < items.length; i++) {
            items[i].style.display = "none";
        }
        menuTitleLi.classList.add("collapsed");
    };

    /**
     * Expand a section: show its nav-items and remove collapsed state.
     */
    Sidebar.prototype._expandSection = function (menuTitleLi) {
        if (!menuTitleLi.classList.contains("collapsed")) return;
        var items = this._getSectionItems(menuTitleLi);
        for (var i = 0; i < items.length; i++) {
            items[i].style.display = "";
        }
        menuTitleLi.classList.remove("collapsed");
    };

    /**
     * On page load, collapse all sections except the one containing
     * the active menu item.
     */
    Sidebar.prototype._collapseInactiveSections = function () {
        var activeLink = this._sidebarEl.querySelector(".menu-link.active");
        var activeSectionTitle = null;

        // Walk backwards from the active link's top-level nav-item to find its section title.
        if (activeLink) {
            var navList = this._sidebarEl.querySelector(".nav-list");
            var topItem = activeLink.closest(".nav-list > .nav-item");
            if (!topItem && navList) {
                // Fallback: walk up to find a nav-item that is a direct child of nav-list.
                var el = activeLink.closest(".nav-item");
                while (el && el.parentElement !== navList) {
                    el = el.parentElement ? el.parentElement.closest(".nav-item") : null;
                }
                topItem = el;
            }
            if (topItem) {
                var prev = topItem.previousElementSibling;
                while (prev) {
                    if (prev.classList.contains("menu-title")) {
                        activeSectionTitle = prev;
                        break;
                    }
                    prev = prev.previousElementSibling;
                }
            }
        }

        var allTitles = this._sidebarEl.querySelectorAll('.menu-title[data-toggle="menu-section"]');
        for (var i = 0; i < allTitles.length; i++) {
            if (allTitles[i] !== activeSectionTitle) {
                this._collapseSection(allTitles[i]);
            }
        }
    };

    /**
     * In small-icon sidebar mode, expand the sidebar on hover and
     * collapse it when the pointer leaves.
     */
    Sidebar.prototype._bindHoverExpand = function () {
        var self = this;

        this._sidebarEl.addEventListener("mouseenter", function () {
            if (self._tm.get("sidebarSize") === "small" && !self._isMobile()) {
                self._hoverExpanded = true;
                document.documentElement.setAttribute("data-sidebar-size", "hover");
                document.body.classList.add("sidebar-hover-active");
            }
        });

        this._sidebarEl.addEventListener("mouseleave", function () {
            if (self._hoverExpanded) {
                self._hoverExpanded = false;
                document.documentElement.setAttribute("data-sidebar-size", "small");
                document.body.classList.remove("sidebar-hover-active");
            }
        });
    };

    /**
     * On window resize, auto-collapse the sidebar when crossing the
     * mobile breakpoint.
     */
    Sidebar.prototype._bindResize = function () {
        var self = this;
        var resizeTimer;

        window.addEventListener("resize", function () {
            clearTimeout(resizeTimer);
            resizeTimer = setTimeout(function () {
                self._handleMobileInit();
            }, 150);
        });
    };

    /**
     * If on mobile, ensure the sidebar starts closed.
     */
    Sidebar.prototype._handleMobileInit = function () {
        if (this._isMobile()) {
            document.body.classList.remove("sidebar-open");
            this._overlay.style.display = "none";
            this._overlay.style.opacity = "0";
        }
    };

    /**
     * Walk the sidebar menu and mark the item whose href matches the
     * current page URL as active. Also expand its parent chain.
     * Implements accordion behavior: only the active menu stays open.
     */
    Sidebar.prototype._highlightActiveItem = function () {
        var currentPath = window.location.pathname;
        var links = this._sidebarEl.querySelectorAll("a");
        var bestMatch = null;
        var bestLength = 0;

        for (var i = 0; i < links.length; i++) {
            var href = links[i].getAttribute("href");
            if (!href || href === "#" || href === "javascript:void(0)") {
                continue;
            }

            // Normalise to a path only.
            try {
                var url = new URL(href, window.location.origin);
                var linkPath = url.pathname;
            } catch (e) {
                continue;
            }

            // Prefer the longest matching prefix so deeper routes win.
            if (
                currentPath === linkPath ||
                (currentPath.indexOf(linkPath) === 0 && linkPath.length > bestLength)
            ) {
                bestMatch = links[i];
                bestLength = linkPath.length;
            }
        }

        // Collapse all open submenus first (accordion on page load).
        var openItems = this._sidebarEl.querySelectorAll(".has-submenu.open, .has-submenu.mm-active, .has-sub.open, .has-sub.mm-active");
        for (var j = 0; j < openItems.length; j++) {
            openItems[j].classList.remove("open", "mm-active");
            var sub = openItems[j].querySelector("ul, .sub-menu, .submenu, .collapse");
            if (sub) {
                sub.style.display = "none";
            }
        }

        if (!bestMatch) {
            return;
        }

        // Mark the link and its ancestors.
        bestMatch.classList.add("active");
        var parentLi = bestMatch.parentElement;
        while (parentLi && parentLi !== this._sidebarEl) {
            if (parentLi.tagName === "LI") {
                parentLi.classList.add("open", "mm-active");
                var sub = parentLi.querySelector("ul, .sub-menu, .submenu, .collapse");
                if (sub) {
                    sub.style.display = "block";
                }
            }
            parentLi = parentLi.parentElement;
        }
    };

    /**
     * @returns {boolean} True if the viewport is at or below mobile width.
     */
    Sidebar.prototype._isMobile = function () {
        return window.innerWidth < MOBILE_BREAKPOINT;
    };

    // -- Public API -----------------------------------------------------------

    /**
     * Toggle sidebar visibility. On mobile this opens/closes with overlay;
     * on desktop it cycles between default and small sidebar sizes.
     */
    Sidebar.prototype.toggle = function () {
        if (this._isMobile()) {
            if (document.body.classList.contains("sidebar-open")) {
                this.close();
            } else {
                this.open();
            }
        } else {
            var current = this._tm.get("sidebarSize");
            if (current === "default") {
                this._tm.setSidebarSize("small");
            } else {
                this._tm.setSidebarSize("default");
            }
        }
    };

    /**
     * Open the sidebar (mobile).
     */
    Sidebar.prototype.open = function () {
        document.body.classList.add("sidebar-open");
        this._overlay.style.display = "block";
        // Force reflow before opacity transition.
        void this._overlay.offsetHeight;
        this._overlay.style.opacity = "1";
    };

    /**
     * Close the sidebar (mobile).
     */
    Sidebar.prototype.close = function () {
        document.body.classList.remove("sidebar-open");
        this._overlay.style.opacity = "0";
        var overlay = this._overlay;
        setTimeout(function () {
            overlay.style.display = "none";
        }, 300);
    };

    // =========================================================================
    // ThemeCustomizer
    // =========================================================================

    /**
     * Controls the slide-out customizer panel. Syncs radio buttons with
     * the ThemeManager state and updates live as settings change.
     *
     * Expected DOM:
     *  - Panel container: #theme-customizer or .theme-customizer
     *  - Open button:     #customizer-toggle or .customizer-toggle
     *  - Close button:    .customizer-close (inside the panel)
     *  - Radio inputs:    input[name="setting-<key>"][value="<value>"]
     *  - Reset button:    #customizer-reset or .customizer-reset
     *
     * @param {ThemeManager} themeManager
     */
    function ThemeCustomizer(themeManager) {
        this._tm = themeManager;
        this._panelEl = null;
        this._init();
    }

    /**
     * Locate the panel, bind events, sync current settings into the
     * radio buttons.
     */
    ThemeCustomizer.prototype._init = function () {
        this._panelEl = document.getElementById("theme-customizer") ||
                        document.querySelector(".theme-customizer");

        if (!this._panelEl) {
            return;
        }

        this._bindToggle();
        this._bindClose();
        this._bindRadios();
        this._bindReset();
        this._syncRadiosToState();

        // Keep radios in sync when settings change externally.
        var self = this;
        this._tm.onChange(function () {
            self._syncRadiosToState();
        });
    };

    /**
     * Bind the gear/toggle button to open the customizer panel.
     */
    ThemeCustomizer.prototype._bindToggle = function () {
        var self = this;
        var toggleBtns = document.querySelectorAll(
            "#customizer-toggle, .customizer-toggle"
        );

        for (var i = 0; i < toggleBtns.length; i++) {
            toggleBtns[i].addEventListener("click", function (e) {
                e.preventDefault();
                self.toggle();
            });
        }
    };

    /**
     * Bind the close button inside the customizer panel.
     */
    ThemeCustomizer.prototype._bindClose = function () {
        var self = this;
        var closeBtns = this._panelEl.querySelectorAll(".customizer-close");

        for (var i = 0; i < closeBtns.length; i++) {
            closeBtns[i].addEventListener("click", function (e) {
                e.preventDefault();
                self.close();
            });
        }
    };

    /**
     * Bind change events on all setting radio inputs.
     * Naming convention: name="setting-<key>" value="<value>".
     */
    ThemeCustomizer.prototype._bindRadios = function () {
        var self = this;

        // Map from radio name suffix to ThemeManager setter.
        var setterMap = {
            theme: "setTheme",
            layout: "setLayout",
            "sidebar-size": "setSidebarSize",
            "sidebar-color": "setSidebarColor",
            "topbar-color": "setTopbarColor",
            "layout-width": "setLayoutWidth",
            "layout-position": "setLayoutPosition",
            direction: "setDirection"
        };

        var radios = this._panelEl.querySelectorAll('input[type="radio"]');

        for (var i = 0; i < radios.length; i++) {
            radios[i].addEventListener("change", function () {
                if (!this.checked) {
                    return;
                }
                var name = this.getAttribute("name") || "";
                var suffix = name.replace(/^setting-/, "");
                var setter = setterMap[suffix];
                if (setter && typeof self._tm[setter] === "function") {
                    self._tm[setter](this.value);
                }
            });
        }

        // Also handle the preloader checkbox/toggle.
        var preloaderToggle = this._panelEl.querySelector(
            'input[name="setting-preloader"]'
        );
        if (preloaderToggle) {
            preloaderToggle.addEventListener("change", function () {
                self._tm.setPreloader(this.checked);
            });
        }
    };

    /**
     * Bind the reset-to-defaults button.
     */
    ThemeCustomizer.prototype._bindReset = function () {
        var self = this;
        var resetBtns = this._panelEl.querySelectorAll(
            "#customizer-reset, .customizer-reset"
        );

        for (var i = 0; i < resetBtns.length; i++) {
            resetBtns[i].addEventListener("click", function (e) {
                e.preventDefault();
                self._tm.resetToDefaults();
            });
        }
    };

    /**
     * Synchronize the radio buttons to reflect the current ThemeManager state.
     */
    ThemeCustomizer.prototype._syncRadiosToState = function () {
        var settings = this._tm.getAll();

        // Map from setting key to radio name suffix.
        var nameMap = {
            theme: "theme",
            layout: "layout",
            sidebarSize: "sidebar-size",
            sidebarColor: "sidebar-color",
            topbarColor: "topbar-color",
            layoutWidth: "layout-width",
            layoutPosition: "layout-position",
            direction: "direction"
        };

        var key, radioName, value, radio;
        for (key in nameMap) {
            if (!nameMap.hasOwnProperty(key)) {
                continue;
            }
            radioName = "setting-" + nameMap[key];
            value = settings[key];
            radio = this._panelEl.querySelector(
                'input[name="' + radioName + '"][value="' + value + '"]'
            );
            if (radio) {
                radio.checked = true;
            }
        }

        // Preloader checkbox.
        var preloaderInput = this._panelEl.querySelector(
            'input[name="setting-preloader"]'
        );
        if (preloaderInput) {
            preloaderInput.checked = !!settings.preloader;
        }
    };

    // -- Public API -----------------------------------------------------------

    /**
     * Toggle the customizer panel open or closed.
     */
    ThemeCustomizer.prototype.toggle = function () {
        if (this._panelEl.classList.contains("open")) {
            this.close();
        } else {
            this.open();
        }
    };

    /**
     * Open the customizer panel.
     */
    ThemeCustomizer.prototype.open = function () {
        this._panelEl.classList.add("open");
    };

    /**
     * Close the customizer panel.
     */
    ThemeCustomizer.prototype.close = function () {
        this._panelEl.classList.remove("open");
    };

    // =========================================================================
    // Utilities
    // =========================================================================

    var Utils = {};

    // ---- CSRF Token Handling ------------------------------------------------

    /**
     * Read a cookie value by name.
     * @param {string} name
     * @returns {string|null}
     */
    Utils.getCookie = function (name) {
        if (!document.cookie || document.cookie === "") {
            return null;
        }
        var cookies = document.cookie.split(";");
        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim();
            if (cookie.indexOf(name + "=") === 0) {
                return decodeURIComponent(cookie.substring(name.length + 1));
            }
        }
        return null;
    };

    /**
     * Get the Django CSRF token from the cookie.
     * @returns {string|null}
     */
    Utils.getCSRFToken = function () {
        return Utils.getCookie("csrftoken");
    };

    /**
     * Determine whether the given HTTP method requires CSRF protection.
     * @param {string} method
     * @returns {boolean}
     */
    Utils._csrfSafeMethod = function (method) {
        return /^(GET|HEAD|OPTIONS|TRACE)$/i.test(method);
    };

    /**
     * Perform a fetch request that automatically includes the Django CSRF
     * token for unsafe methods. Returns a Promise.
     *
     * @param {string} url
     * @param {Object} [options]  - Standard fetch options. Defaults to POST
     *                              with JSON content type.
     * @returns {Promise<Response>}
     */
    Utils.fetchJSON = function (url, options) {
        options = options || {};
        var method = (options.method || "POST").toUpperCase();

        var headers = options.headers || {};
        if (!headers["Content-Type"] && method !== "GET") {
            headers["Content-Type"] = "application/json";
        }
        if (!Utils._csrfSafeMethod(method)) {
            var token = Utils.getCSRFToken();
            if (token) {
                headers["X-CSRFToken"] = token;
            }
        }

        options.headers = headers;
        if (typeof options.credentials === "undefined") {
            options.credentials = "same-origin";
        }

        return fetch(url, options).then(function (response) {
            if (!response.ok) {
                throw new Error("HTTP " + response.status + ": " + response.statusText);
            }
            var ct = response.headers.get("content-type") || "";
            if (ct.indexOf("application/json") !== -1) {
                return response.json();
            }
            return response.text();
        });
    };

    /**
     * Set up the CSRF token on the legacy XMLHttpRequest for any code that
     * uses jQuery-style $.ajax. Also configures a global XMLHttpRequest
     * wrapper when jQuery is not present.
     */
    Utils.setupAjaxCSRF = function () {
        // jQuery integration.
        if (typeof jQuery !== "undefined") {
            jQuery.ajaxSetup({
                beforeSend: function (xhr, settings) {
                    if (!Utils._csrfSafeMethod(settings.type) && !this.crossDomain) {
                        var token = Utils.getCSRFToken();
                        if (token) {
                            xhr.setRequestHeader("X-CSRFToken", token);
                        }
                    }
                }
            });
        }
    };

    // ---- Preloader ----------------------------------------------------------

    /**
     * Fade out and remove the preloader element.
     * Call this on DOMContentLoaded or window.load.
     */
    Utils.hidePreloader = function () {
        var el = document.getElementById("preloader");
        if (!el) {
            return;
        }
        el.style.transition = "opacity 0.4s ease";
        el.style.opacity = "0";
        setTimeout(function () {
            el.style.display = "none";
        }, 400);
    };

    // ---- Tooltips & Popovers ------------------------------------------------

    /**
     * Initialize Bootstrap tooltips and popovers if Bootstrap 5 JS is loaded.
     */
    Utils.initTooltipsAndPopovers = function () {
        if (typeof bootstrap === "undefined") {
            return;
        }

        // Tooltips.
        var tooltipEls = document.querySelectorAll('[data-bs-toggle="tooltip"]');
        for (var i = 0; i < tooltipEls.length; i++) {
            new bootstrap.Tooltip(tooltipEls[i]);
        }

        // Popovers.
        var popoverEls = document.querySelectorAll('[data-bs-toggle="popover"]');
        for (var j = 0; j < popoverEls.length; j++) {
            new bootstrap.Popover(popoverEls[j]);
        }
    };

    // ---- Toast Notifications ------------------------------------------------

    /**
     * Show a toast notification.
     *
     * @param {string} message   - The message body.
     * @param {Object} [opts]    - Options.
     * @param {"success"|"error"|"warning"|"info"} [opts.type="info"]
     * @param {string}  [opts.title]     - Optional title line.
     * @param {number}  [opts.duration]  - Auto-hide in ms (0 = manual close). Default 5000.
     * @param {string}  [opts.position]  - CSS class for placement. Default "top-0 end-0".
     */
    Utils.toast = function (message, opts) {
        opts = opts || {};
        var type = opts.type || "info";
        var title = opts.title || type.charAt(0).toUpperCase() + type.slice(1);
        var duration = typeof opts.duration === "number" ? opts.duration : 5000;
        var position = opts.position || "top-0 end-0";

        // Icon mapping.
        var iconMap = {
            success: "bi-check-circle-fill",
            error: "bi-x-circle-fill",
            warning: "bi-exclamation-triangle-fill",
            info: "bi-info-circle-fill"
        };
        var bgMap = {
            success: "#198754",
            error: "#dc3545",
            warning: "#ffc107",
            info: "#0dcaf0"
        };

        // Ensure a toast container exists.
        var containerId = "navhcm-toast-container";
        var container = document.getElementById(containerId);
        if (!container) {
            container = document.createElement("div");
            container.id = containerId;
            container.className = "toast-container position-fixed p-3 " + position;
            container.style.zIndex = "9999";
            document.body.appendChild(container);
        }

        // Build the toast element.
        var toastEl = document.createElement("div");
        toastEl.className = "toast align-items-center border-0 show";
        toastEl.setAttribute("role", "alert");
        toastEl.setAttribute("aria-live", "assertive");
        toastEl.setAttribute("aria-atomic", "true");
        toastEl.style.minWidth = "280px";

        var iconClass = iconMap[type] || iconMap.info;
        var bgColor = bgMap[type] || bgMap.info;
        var textColor = type === "warning" ? "#000" : "#fff";

        toastEl.innerHTML =
            '<div style="background:' + bgColor + ';color:' + textColor + ';" ' +
            'class="toast-header border-0">' +
            '<i class="bi ' + iconClass + ' me-2"></i>' +
            '<strong class="me-auto">' + _escapeHtml(title) + '</strong>' +
            '<button type="button" class="btn-close btn-close-white" ' +
            'data-dismiss="toast" aria-label="Close"></button>' +
            '</div>' +
            '<div class="toast-body" style="background:' + bgColor + ';color:' +
            textColor + ';border-radius:0 0 .375rem .375rem;">' +
            _escapeHtml(message) +
            '</div>';

        container.appendChild(toastEl);

        // Close button handler.
        var closeBtn = toastEl.querySelector('[data-dismiss="toast"]');
        if (closeBtn) {
            closeBtn.addEventListener("click", function () {
                _removeToast(toastEl);
            });
        }

        // Also try Bootstrap Toast API if available.
        if (typeof bootstrap !== "undefined" && bootstrap.Toast) {
            try {
                var bsToast = new bootstrap.Toast(toastEl, {
                    autohide: duration > 0,
                    delay: duration
                });
                bsToast.show();
                toastEl.addEventListener("hidden.bs.toast", function () {
                    _removeToast(toastEl);
                });
                return;
            } catch (e) {
                // Fallback to manual handling below.
            }
        }

        // Manual auto-hide.
        if (duration > 0) {
            setTimeout(function () {
                _removeToast(toastEl);
            }, duration);
        }
    };

    /**
     * Remove a toast element with a fade animation.
     * @param {HTMLElement} el
     */
    function _removeToast(el) {
        if (!el || !el.parentNode) {
            return;
        }
        el.style.transition = "opacity 0.3s";
        el.style.opacity = "0";
        setTimeout(function () {
            if (el.parentNode) {
                el.parentNode.removeChild(el);
            }
        }, 300);
    }

    /**
     * Escape HTML entities in a string to prevent XSS.
     * @param {string} str
     * @returns {string}
     */
    function _escapeHtml(str) {
        var div = document.createElement("div");
        div.appendChild(document.createTextNode(str));
        return div.innerHTML;
    }

    // ---- Confirm Dialog for Delete Actions ----------------------------------

    /**
     * Show a confirmation dialog before performing a destructive action.
     * Uses a Bootstrap modal if available, otherwise falls back to
     * window.confirm.
     *
     * @param {Object}   opts
     * @param {string}   [opts.title]    - Dialog title. Default "Confirm Delete".
     * @param {string}   [opts.message]  - Body text.
     * @param {string}   [opts.confirmText] - Confirm button label. Default "Delete".
     * @param {string}   [opts.cancelText]  - Cancel button label. Default "Cancel".
     * @param {Function} opts.onConfirm  - Called when the user confirms.
     * @param {Function} [opts.onCancel] - Called when the user cancels.
     */
    Utils.confirmDelete = function (opts) {
        opts = opts || {};
        var title = opts.title || "Confirm Delete";
        var message = opts.message || "Are you sure you want to delete this item? This action cannot be undone.";
        var confirmText = opts.confirmText || "Delete";
        var cancelText = opts.cancelText || "Cancel";

        // Try Bootstrap Modal.
        if (typeof bootstrap !== "undefined" && bootstrap.Modal) {
            _showBootstrapConfirm(title, message, confirmText, cancelText, opts);
            return;
        }

        // Fallback to native confirm.
        if (window.confirm(message)) {
            if (typeof opts.onConfirm === "function") {
                opts.onConfirm();
            }
        } else {
            if (typeof opts.onCancel === "function") {
                opts.onCancel();
            }
        }
    };

    /**
     * Build and show a Bootstrap 5 modal for confirmation.
     */
    function _showBootstrapConfirm(title, message, confirmText, cancelText, opts) {
        var modalId = "navhcm-confirm-modal";

        // Remove any existing instance.
        var existing = document.getElementById(modalId);
        if (existing) {
            existing.remove();
        }

        var modalHtml =
            '<div class="modal fade" id="' + modalId + '" tabindex="-1" ' +
            'aria-labelledby="' + modalId + '-label" aria-hidden="true">' +
            '<div class="modal-dialog modal-dialog-centered">' +
            '<div class="modal-content">' +
            '<div class="modal-header">' +
            '<h5 class="modal-title" id="' + modalId + '-label">' +
            _escapeHtml(title) + '</h5>' +
            '<button type="button" class="btn-close" data-bs-dismiss="modal" ' +
            'aria-label="Close"></button>' +
            '</div>' +
            '<div class="modal-body">' +
            '<p class="mb-0">' + _escapeHtml(message) + '</p>' +
            '</div>' +
            '<div class="modal-footer">' +
            '<button type="button" class="btn btn-light" data-bs-dismiss="modal">' +
            _escapeHtml(cancelText) + '</button>' +
            '<button type="button" class="btn btn-danger" id="' + modalId + '-confirm">' +
            _escapeHtml(confirmText) + '</button>' +
            '</div></div></div></div>';

        var wrapper = document.createElement("div");
        wrapper.innerHTML = modalHtml;
        var modalEl = wrapper.firstChild;
        document.body.appendChild(modalEl);

        var modal = new bootstrap.Modal(modalEl);

        var confirmBtn = document.getElementById(modalId + "-confirm");
        confirmBtn.addEventListener("click", function () {
            modal.hide();
            if (typeof opts.onConfirm === "function") {
                opts.onConfirm();
            }
        });

        modalEl.addEventListener("hidden.bs.modal", function () {
            modalEl.remove();
        });

        // If the user dismisses without confirming, fire onCancel.
        var confirmed = false;
        confirmBtn.addEventListener("click", function () {
            confirmed = true;
        });
        modalEl.addEventListener("hidden.bs.modal", function () {
            if (!confirmed && typeof opts.onCancel === "function") {
                opts.onCancel();
            }
        });

        modal.show();
    }

    // ---- DataTable-like Search/Filter for Tables ----------------------------

    /**
     * Attach a live search/filter to a table.
     *
     * @param {Object} opts
     * @param {string|HTMLElement} opts.table  - Selector or element for the <table>.
     * @param {string|HTMLElement} opts.input  - Selector or element for the search <input>.
     * @param {number[]}          [opts.columns] - Column indices to search (0-based).
     *                                             Defaults to all columns.
     * @param {string}            [opts.noResultsText] - Text shown when nothing matches.
     * @returns {Object} Controller with .refresh() and .destroy() methods.
     */
    Utils.tableFilter = function (opts) {
        opts = opts || {};

        var tableEl = typeof opts.table === "string"
            ? document.querySelector(opts.table)
            : opts.table;
        var inputEl = typeof opts.input === "string"
            ? document.querySelector(opts.input)
            : opts.input;

        if (!tableEl || !inputEl) {
            return null;
        }

        var tbody = tableEl.querySelector("tbody");
        if (!tbody) {
            return null;
        }

        var noResultsText = opts.noResultsText || "No matching records found.";
        var searchColumns = opts.columns || null;
        var noResultsRow = null;

        function getSearchableText(row) {
            var cells = row.querySelectorAll("td");
            var parts = [];
            for (var i = 0; i < cells.length; i++) {
                if (searchColumns === null || searchColumns.indexOf(i) !== -1) {
                    parts.push((cells[i].textContent || "").toLowerCase());
                }
            }
            return parts.join(" ");
        }

        function applyFilter() {
            var query = (inputEl.value || "").toLowerCase().trim();
            var rows = tbody.querySelectorAll("tr:not(.table-filter-no-results)");
            var visibleCount = 0;

            for (var i = 0; i < rows.length; i++) {
                var text = getSearchableText(rows[i]);
                if (query === "" || text.indexOf(query) !== -1) {
                    rows[i].style.display = "";
                    visibleCount++;
                } else {
                    rows[i].style.display = "none";
                }
            }

            // Show/hide "no results" row.
            if (visibleCount === 0) {
                if (!noResultsRow) {
                    noResultsRow = document.createElement("tr");
                    noResultsRow.className = "table-filter-no-results";
                    var colCount = tableEl.querySelectorAll("thead th").length ||
                                   (rows[0] ? rows[0].querySelectorAll("td").length : 1);
                    var td = document.createElement("td");
                    td.setAttribute("colspan", colCount);
                    td.className = "text-center text-muted py-4";
                    td.textContent = noResultsText;
                    noResultsRow.appendChild(td);
                }
                if (!noResultsRow.parentNode) {
                    tbody.appendChild(noResultsRow);
                }
                noResultsRow.style.display = "";
            } else if (noResultsRow) {
                noResultsRow.style.display = "none";
            }
        }

        // Debounced input handler.
        var debounceTimer;
        function onInput() {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(applyFilter, 200);
        }

        inputEl.addEventListener("input", onInput);
        inputEl.addEventListener("keyup", onInput);

        // Run once on init in case the input already has a value.
        applyFilter();

        return {
            /** Re-run the filter (e.g. after adding rows dynamically). */
            refresh: applyFilter,

            /** Remove the filter and restore all rows. */
            destroy: function () {
                inputEl.removeEventListener("input", onInput);
                inputEl.removeEventListener("keyup", onInput);
                clearTimeout(debounceTimer);
                var rows = tbody.querySelectorAll("tr");
                for (var i = 0; i < rows.length; i++) {
                    rows[i].style.display = "";
                }
                if (noResultsRow && noResultsRow.parentNode) {
                    noResultsRow.parentNode.removeChild(noResultsRow);
                }
            }
        };
    };

    // =========================================================================
    // Auto-bind delete confirmation to elements
    // =========================================================================

    /**
     * Bind confirmation dialogs to all elements marked with
     * data-confirm-delete. The element's href or data-url is used for
     * a POST request on confirmation.
     */
    function _bindDeleteConfirmations() {
        var triggers = document.querySelectorAll("[data-confirm-delete]");
        for (var i = 0; i < triggers.length; i++) {
            (function (el) {
                el.addEventListener("click", function (e) {
                    e.preventDefault();
                    var url = el.getAttribute("data-url") || el.getAttribute("href");
                    var message = el.getAttribute("data-confirm-message") ||
                                  "Are you sure you want to delete this item? This action cannot be undone.";
                    var title = el.getAttribute("data-confirm-title") || "Confirm Delete";

                    Utils.confirmDelete({
                        title: title,
                        message: message,
                        onConfirm: function () {
                            if (url) {
                                Utils.fetchJSON(url, { method: "POST" })
                                    .then(function () {
                                        // Remove the closest table row or parent element.
                                        var row = el.closest("tr");
                                        if (row) {
                                            row.style.transition = "opacity 0.3s";
                                            row.style.opacity = "0";
                                            setTimeout(function () {
                                                row.remove();
                                            }, 300);
                                        } else {
                                            window.location.reload();
                                        }
                                        Utils.toast("Item deleted successfully.", {
                                            type: "success"
                                        });
                                    })
                                    .catch(function (err) {
                                        Utils.toast(
                                            "Failed to delete: " + err.message,
                                            { type: "error" }
                                        );
                                    });
                            }
                        }
                    });
                });
            })(triggers[i]);
        }
    }

    // =========================================================================
    // Dark Mode Toggle
    // =========================================================================

    function _bindDarkModeToggle(themeManager) {
        var btn = document.getElementById("light-dark-mode-btn") ||
                  document.querySelector(".light-dark-mode");
        if (!btn) return;

        function updateIcon() {
            var isDark = themeManager.get("theme") === "dark";
            var darkIcon = document.getElementById("theme-icon-dark");
            var lightIcon = document.getElementById("theme-icon-light");
            if (darkIcon) darkIcon.classList.toggle("d-none", isDark);
            if (lightIcon) lightIcon.classList.toggle("d-none", !isDark);
        }

        btn.addEventListener("click", function (e) {
            e.preventDefault();
            themeManager.toggleTheme();
            updateIcon();
        });

        themeManager.onChange(function (key) {
            if (key === "theme" || key === "*") updateIcon();
        });

        updateIcon();
    }

    // =========================================================================
    // Fullscreen Toggle
    // =========================================================================

    function _bindFullscreenToggle() {
        var btns = document.querySelectorAll('[data-toggle="fullscreen"]');
        for (var i = 0; i < btns.length; i++) {
            btns[i].addEventListener("click", function (e) {
                e.preventDefault();
                if (!document.fullscreenElement) {
                    document.documentElement.requestFullscreen().catch(function () {});
                } else {
                    document.exitFullscreen().catch(function () {});
                }
            });
        }
    }

    // =========================================================================
    // Search Box
    // =========================================================================

    function _bindSearchBox() {
        var input = document.getElementById("search-options");
        var dropdown = document.getElementById("search-dropdown");
        var closeBtn = document.getElementById("search-close-options");
        if (!input || !dropdown) return;

        // Build search data from sidebar links.
        var searchData = [];
        var sidebarLinks = document.querySelectorAll(".app-menu .menu-link[href]");
        for (var i = 0; i < sidebarLinks.length; i++) {
            var href = sidebarLinks[i].getAttribute("href");
            if (!href || href === "#" || href === "javascript:void(0);") continue;
            var text = (sidebarLinks[i].textContent || "").trim();
            var icon = sidebarLinks[i].querySelector("i");
            var iconClass = icon ? icon.className : "ri-link";
            if (text) {
                searchData.push({ text: text, href: href, icon: iconClass });
            }
        }

        function renderResults(query) {
            if (!query) {
                dropdown.classList.remove("show");
                dropdown.innerHTML = "";
                return;
            }
            var q = query.toLowerCase();
            var matches = [];
            for (var i = 0; i < searchData.length; i++) {
                if (searchData[i].text.toLowerCase().indexOf(q) !== -1) {
                    matches.push(searchData[i]);
                }
            }
            if (matches.length === 0) {
                dropdown.innerHTML = '<div class="p-3 text-center text-muted"><i class="ri-search-line d-block mb-1" style="font-size:20px;opacity:.4"></i>No results found</div>';
            } else {
                var html = "";
                for (var j = 0; j < matches.length && j < 8; j++) {
                    html += '<a href="' + matches[j].href + '" class="dropdown-item d-flex align-items-center gap-2 py-2">' +
                            '<i class="' + matches[j].icon.split(" ")[0] + ' text-muted"></i>' +
                            '<span>' + _escapeHtml(matches[j].text) + '</span></a>';
                }
                dropdown.innerHTML = html;
            }
            dropdown.classList.add("show");
        }

        var debounce;
        input.addEventListener("input", function () {
            clearTimeout(debounce);
            var val = input.value.trim();
            debounce = setTimeout(function () {
                renderResults(val);
            }, 150);
            if (closeBtn) {
                closeBtn.classList.toggle("d-none", !val);
            }
        });

        input.addEventListener("focus", function () {
            if (input.value.trim()) renderResults(input.value.trim());
        });

        if (closeBtn) {
            closeBtn.addEventListener("click", function () {
                input.value = "";
                dropdown.classList.remove("show");
                closeBtn.classList.add("d-none");
            });
        }

        document.addEventListener("click", function (e) {
            if (!input.contains(e.target) && !dropdown.contains(e.target)) {
                dropdown.classList.remove("show");
            }
        });
    }

    // =========================================================================
    // Initialization
    // =========================================================================

    /**
     * Primary initialization. Called on DOMContentLoaded.
     */
    function init() {
        // 1. Theme Manager (applies saved settings to DOM immediately).
        var themeManager = new ThemeManager();

        // 2. Sidebar.
        var sidebar = new Sidebar(themeManager);

        // 3. Theme Customizer panel.
        var customizer = new ThemeCustomizer(themeManager);

        // 4. Preloader fade-out.
        Utils.hidePreloader();

        // 5. CSRF setup for AJAX.
        Utils.setupAjaxCSRF();

        // 6. Tooltips and popovers.
        Utils.initTooltipsAndPopovers();

        // 7. Auto-bind delete confirmations.
        _bindDeleteConfirmations();

        // 8. Auto-initialize table filters.
        var filterInputs = document.querySelectorAll("[data-table-filter]");
        for (var i = 0; i < filterInputs.length; i++) {
            var targetSelector = filterInputs[i].getAttribute("data-table-filter");
            Utils.tableFilter({
                table: targetSelector,
                input: filterInputs[i]
            });
        }

        // 9. Dark mode toggle button.
        _bindDarkModeToggle(themeManager);

        // 10. Fullscreen toggle.
        _bindFullscreenToggle();

        // 11. Search box.
        _bindSearchBox();

        // Expose key objects on the global NavHCM namespace.
        window.NavHCM = {
            themeManager: themeManager,
            sidebar: sidebar,
            customizer: customizer,
            utils: Utils,
            version: "1.0.0"
        };
    }

    // =========================================================================
    // Bootstrap
    // =========================================================================

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        // DOM already ready (e.g. script loaded with defer or at bottom of body).
        init();
    }

})();
