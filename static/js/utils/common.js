/**
 * Common JavaScript Utilities
 * Shared functionality used across the application following DRY principles
 */

/**
 * Bootstrap Utilities
 */
const BootstrapUtils = {
    /**
     * Initialize all Bootstrap tooltips on the page
     * @param {string} selector - Optional selector for tooltip elements
     */
    initializeTooltips(selector = '[data-bs-toggle="tooltip"]') {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll(selector));
        return tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    },

    /**
     * Refresh a tooltip after content change
     * @param {HTMLElement} element - The element with tooltip
     */
    refreshTooltip(element) {
        const existingTooltip = bootstrap.Tooltip.getInstance(element);
        if (existingTooltip) {
            existingTooltip.dispose();
        }
        return new bootstrap.Tooltip(element);
    },

    /**
     * Auto-dismiss alerts with smooth fade
     * @param {number} delay - Delay in milliseconds before dismissing
     * @param {number} fadeTime - Fade out time in milliseconds
     */
    autoDismissAlerts(delay = 3000, fadeTime = 800) {
        const alerts = document.querySelectorAll('.alert-dismissible');
        alerts.forEach(function(alert) {
            setTimeout(function() {
                alert.style.transition = `opacity ${fadeTime}ms ease-out`;
                alert.style.opacity = '0';
                
                setTimeout(function() {
                    const bsAlert = new bootstrap.Alert(alert);
                    bsAlert.close();
                }, fadeTime);
            }, delay);
        });
    }
};

/**
 * DOM Utilities
 */
const DOMUtils = {
    /**
     * Safely execute a function when DOM is ready
     * @param {Function} callback - Function to execute
     */
    ready(callback) {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', callback);
        } else {
            callback();
        }
    },

    /**
     * Get element by ID with null check
     * @param {string} id - Element ID
     * @returns {HTMLElement|null}
     */
    safeGetById(id) {
        return document.getElementById(id);
    },

    /**
     * Get element by selector with null check
     * @param {string} selector - CSS selector
     * @returns {HTMLElement|null}
     */
    safeQuerySelector(selector) {
        return document.querySelector(selector);
    },

    /**
     * Get all elements by selector
     * @param {string} selector - CSS selector
     * @returns {NodeList}
     */
    safeQuerySelectorAll(selector) {
        return document.querySelectorAll(selector) || [];
    }
};

/**
 * Collapse/Expand Utilities
 */
const CollapseUtils = {
    /**
     * Setup chevron rotation for collapse elements
     * @param {string} selector - Selector for collapse trigger elements
     * @param {string} excludeSelector - Optional selector to exclude
     */
    setupChevronRotation(selector = '[data-bs-toggle="collapse"]', excludeSelector = null) {
        let elements = DOMUtils.safeQuerySelectorAll(selector);
        
        if (excludeSelector) {
            elements = Array.from(elements).filter(el => !el.matches(excludeSelector));
        }
        
        elements.forEach(function(element) {
            const target = DOMUtils.safeQuerySelector(element.getAttribute('data-bs-target'));
            if (!target) return;
            
            const chevron = element.querySelector('i');
            if (!chevron) return;
            
            target.addEventListener('show.bs.collapse', function () {
                chevron.classList.remove('bi-caret-down');
                chevron.classList.add('bi-caret-up');
                element.setAttribute('aria-expanded', 'true');
            });
            
            target.addEventListener('hide.bs.collapse', function () {
                chevron.classList.remove('bi-caret-up');
                chevron.classList.add('bi-caret-down');
                element.setAttribute('aria-expanded', 'false');
            });
        });
    },

    /**
     * Generic expand/collapse all functionality
     * @param {Object} config - Configuration object
     * @param {string} config.toggleButtonId - ID of the toggle all button
     * @param {string} config.targetSelector - Selector for elements to toggle
     * @param {string} config.expandText - Text to show when collapsed
     * @param {string} config.collapseText - Text to show when expanded
     * @param {string} config.expandIcon - Icon class for expand state
     * @param {string} config.collapseIcon - Icon class for collapse state
     * @param {string} config.expandTooltip - Tooltip for expand state
     * @param {string} config.collapseTooltip - Tooltip for collapse state
     */
    setupToggleAll(config) {
        const toggleBtn = DOMUtils.safeGetById(config.toggleButtonId);
        if (!toggleBtn) return;

        toggleBtn.addEventListener('click', function() {
            const targets = DOMUtils.safeQuerySelectorAll(config.targetSelector);
            const toggleIcon = this.querySelector('i');
            
            const isCurrentlyCollapsed = toggleIcon.classList.contains(config.expandIcon);
            
            targets.forEach(function(target) {
                const bsCollapse = bootstrap.Collapse.getOrCreateInstance(target);
                if (isCurrentlyCollapsed) {
                    bsCollapse.show();
                } else {
                    bsCollapse.hide();
                }
            });
            
            // Update button state
            if (isCurrentlyCollapsed) {
                toggleIcon.className = `bi ${config.collapseIcon}`;
                this.setAttribute('title', config.collapseTooltip);
                if (config.collapseText) {
                    this.innerHTML = `<i class="bi ${config.collapseIcon}"></i> ${config.collapseText}`;
                }
            } else {
                toggleIcon.className = `bi ${config.expandIcon}`;
                this.setAttribute('title', config.expandTooltip);
                if (config.expandText) {
                    this.innerHTML = `<i class="bi ${config.expandIcon}"></i> ${config.expandText}`;
                }
            }
            
            BootstrapUtils.refreshTooltip(this);
        });
    }
};

// Export utilities to global scope
window.BootstrapUtils = BootstrapUtils;
window.DOMUtils = DOMUtils;
window.CollapseUtils = CollapseUtils;