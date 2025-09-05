/**
 * Table Sorting Utility
 * Reusable table sorting functionality with Bootstrap icons
 */

class TableSorter {
    constructor(tableId) {
        this.table = document.getElementById(tableId);
        this.tbody = this.table.querySelector('tbody');
        this.sortDirection = {};
        this.columnConfigs = {};
    }

    /**
     * Configure column sorting behavior
     * @param {number} columnIndex - The column index
     * @param {Object} config - Configuration object
     * @param {string} config.type - 'text', 'numeric', 'badge-text', 'badge-numeric', 'assignment-id'
     * @param {Function} config.extractor - Custom function to extract sortable value
     */
    configureColumn(columnIndex, config) {
        this.columnConfigs[columnIndex] = config;
    }

    /**
     * Sort table by column
     * @param {number} columnIndex - The column to sort by
     */
    sortTable(columnIndex) {
        if (!this.table || !this.tbody) {
            console.error('Table or tbody not found');
            return;
        }

        const rows = Array.from(this.tbody.querySelectorAll('tr'));
        
        // Toggle sort direction for this column
        this.sortDirection[columnIndex] = !this.sortDirection[columnIndex];
        const ascending = this.sortDirection[columnIndex];
        
        // Update header icons
        this.updateHeaderIcons(columnIndex, ascending);
        
        // Sort rows
        rows.sort((a, b) => {
            const cellA = a.cells[columnIndex];
            const cellB = b.cells[columnIndex];
            
            let valueA, valueB;
            
            // Use custom extractor or default extraction
            const config = this.columnConfigs[columnIndex];
            if (config && config.extractor) {
                valueA = config.extractor(cellA);
                valueB = config.extractor(cellB);
            } else {
                [valueA, valueB] = this.extractValues(cellA, cellB, columnIndex);
            }
            
            // Compare values
            if (config && config.type === 'numeric' || 
                (config && config.type === 'badge-numeric') ||
                typeof valueA === 'number') {
                return ascending ? valueA - valueB : valueB - valueA;
            } else {
                return ascending ? 
                    String(valueA).localeCompare(String(valueB)) : 
                    String(valueB).localeCompare(String(valueA));
            }
        });
        
        // Clear tbody and append sorted rows
        this.tbody.innerHTML = '';
        rows.forEach(row => this.tbody.appendChild(row));
    }

    /**
     * Extract values from cells based on column configuration
     */
    extractValues(cellA, cellB, columnIndex) {
        const config = this.columnConfigs[columnIndex];
        
        if (!config) {
            // Default: plain text
            return [cellA.textContent.trim(), cellB.textContent.trim()];
        }

        switch (config.type) {
            case 'assignment-id':
                // Extract from <strong> tag
                const strongA = cellA.querySelector('strong');
                const strongB = cellB.querySelector('strong');
                return [
                    strongA ? strongA.textContent.trim() : '',
                    strongB ? strongB.textContent.trim() : ''
                ];

            case 'badge-text':
                // Extract text from badge
                const badgeA = cellA.querySelector('.badge');
                const badgeB = cellB.querySelector('.badge');
                return [
                    badgeA ? badgeA.textContent.trim() : '',
                    badgeB ? badgeB.textContent.trim() : ''
                ];

            case 'badge-numeric':
                // Extract number from badge text
                const badgeNumA = cellA.querySelector('.badge');
                const badgeNumB = cellB.querySelector('.badge');
                const matchA = badgeNumA ? badgeNumA.textContent.match(/\d+/) : null;
                const matchB = badgeNumB ? badgeNumB.textContent.match(/\d+/) : null;
                return [
                    matchA ? parseInt(matchA[0]) : 0,
                    matchB ? parseInt(matchB[0]) : 0
                ];

            case 'numeric':
                // Parse as float, remove 'h' suffix if present
                const textA = cellA.textContent.replace('h', '').trim();
                const textB = cellB.textContent.replace('h', '').trim();
                return [
                    parseFloat(textA) || 0,
                    parseFloat(textB) || 0
                ];

            case 'text':
            default:
                return [cellA.textContent.trim(), cellB.textContent.trim()];
        }
    }

    /**
     * Update header icons to show sort direction
     */
    updateHeaderIcons(columnIndex, ascending) {
        // Reset all icons
        const headers = this.table.querySelectorAll('th i');
        headers.forEach(icon => {
            icon.className = 'bi bi-arrow-down-up';
        });
        
        // Set current column icon
        const currentIcon = this.table.querySelectorAll('th')[columnIndex].querySelector('i');
        if (currentIcon) {
            currentIcon.className = ascending ? 'bi bi-arrow-up' : 'bi bi-arrow-down';
        }
    }

    /**
     * Set default sort column
     * @param {number} columnIndex - Column to sort by default
     */
    setDefaultSort(columnIndex) {
        // Set initial direction to false so first sort will be ascending
        this.sortDirection[columnIndex] = false;
        this.sortTable(columnIndex);
    }
}

// Export for use in other modules
window.TableSorter = TableSorter;
