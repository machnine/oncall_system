/**
 * Monthly Report Table Sorting
 * Uses TableSorter utility for table sorting functionality
 */

let reportTableSorter;

// Default sort by Assignment ID on page load
document.addEventListener('DOMContentLoaded', function() {
    // Initialize TableSorter
    reportTableSorter = new TableSorter('reportTable');
    
    // Configure columns
    reportTableSorter.configureColumn(0, { type: 'text' }); // Assignment ID - text
    reportTableSorter.configureColumn(1, { type: 'text' }); // Name - text
    // Columns 2+ are numeric (Weekday, Saturday, etc.)
    for (let i = 2; i < 10; i++) { // Assuming max 10 columns
        reportTableSorter.configureColumn(i, { type: 'numeric' });
    }
    
    // Set default sort
    reportTableSorter.setDefaultSort(0);
});

// Global function for template onclick handlers
function sortTable(columnIndex) {
    if (reportTableSorter) {
        reportTableSorter.sortTable(columnIndex);
    }
}
