/**
 * Timeblocks Table JavaScript
 * Handles hover effects, tooltips, and expand/collapse functionality
 */

DOMUtils.ready(function() {
    // Initialize Bootstrap tooltips
    BootstrapUtils.initializeTooltips();

    // Show/hide action buttons on row hover (only for non-admin views)
    // This function will be called with isAdminView parameter
    function initializeHoverEffects(isAdminView) {
        if (!isAdminView) {
            // Show/hide action buttons on row hover
            document.querySelectorAll('tbody tr').forEach(function(row) {
                // Skip collapsed detail rows
                if (row.classList.contains('collapse')) return;
                
                row.addEventListener('mouseenter', function() {
                    const actions = this.querySelector('.block-actions, .entry-actions');
                    if (actions) {
                        actions.style.opacity = '1';
                    }
                });
                
                row.addEventListener('mouseleave', function() {
                    const actions = this.querySelector('.block-actions, .entry-actions');
                    if (actions) {
                        actions.style.opacity = '0';
                    }
                });
            });

            // Handle hover for nested time entry rows
            document.querySelectorAll('.collapse tbody tr').forEach(function(row) {
                row.addEventListener('mouseenter', function() {
                    const actions = this.querySelector('.entry-actions');
                    if (actions) {
                        actions.style.opacity = '1';
                    }
                });
                
                row.addEventListener('mouseleave', function() {
                    const actions = this.querySelector('.entry-actions');
                    if (actions) {
                        actions.style.opacity = '0';
                    }
                });
            });
        }
    }

    // Handle chevron rotation on collapse toggle
    CollapseUtils.setupChevronRotation('[data-bs-toggle="collapse"]', '#toggleAllBlocks');

    // Handle toggle all blocks
    CollapseUtils.setupToggleAll({
        toggleButtonId: 'toggleAllBlocks',
        targetSelector: '[id^="block-"]',
        expandIcon: 'bi-caret-down',
        collapseIcon: 'bi-caret-up',
        expandTooltip: 'Expand all blocks',
        collapseTooltip: 'Collapse all blocks'
    });

    // Expose the initialization function globally
    window.initializeTimeblocksHoverEffects = initializeHoverEffects;
});