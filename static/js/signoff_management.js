/**
 * Signoff Management Table Sorting
 * Uses TableSorter utility for table sorting functionality
 */

let signoffTableSorter;

// Default sort by Staff ID on page load
document.addEventListener('DOMContentLoaded', function() {
    // Initialize TableSorter
    signoffTableSorter = new TableSorter('signoffTable');
    
    // Configure columns
    signoffTableSorter.configureColumn(0, { type: 'assignment-id' }); // Staff column - sort by assignment ID in <strong>
    signoffTableSorter.configureColumn(1, { type: 'badge-numeric' }); // Time Blocks column - extract number from badge
    signoffTableSorter.configureColumn(2, { type: 'numeric' }); // Hours column - numeric with 'h' suffix
    signoffTableSorter.configureColumn(3, { type: 'numeric' }); // Claims column - numeric with 'h' suffix  
    signoffTableSorter.configureColumn(4, { type: 'badge-text' }); // Status column - sort by badge text
    
    // Set default sort
    signoffTableSorter.setDefaultSort(0);
});

// Global function for template onclick handlers
function sortTable(columnIndex) {
    if (signoffTableSorter) {
        signoffTableSorter.sortTable(columnIndex);
    }
}
