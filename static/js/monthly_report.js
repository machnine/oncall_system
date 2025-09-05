/**
 * Monthly Report Table Sorting
 * Handles table sorting functionality for the monthly report page
 */

let sortDirection = {};

function sortTable(columnIndex) {
    const table = document.getElementById('reportTable');
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    // Toggle sort direction for this column
    sortDirection[columnIndex] = !sortDirection[columnIndex];
    const ascending = sortDirection[columnIndex];
    
    // Update header icons
    const headers = table.querySelectorAll('th i');
    headers.forEach(icon => {
        icon.className = 'bi bi-arrow-down-up';
    });
    
    const currentIcon = table.querySelectorAll('th')[columnIndex].querySelector('i');
    currentIcon.className = ascending ? 'bi bi-arrow-up' : 'bi bi-arrow-down';
    
    // Sort rows
    rows.sort((a, b) => {
        const cellA = a.cells[columnIndex].textContent.trim();
        const cellB = b.cells[columnIndex].textContent.trim();
        
        // Check if values are numeric (for hours columns)
        if (columnIndex >= 2) { // Numeric columns (Weekday, Saturday, etc.)
            const numA = parseFloat(cellA) || 0;
            const numB = parseFloat(cellB) || 0;
            return ascending ? numA - numB : numB - numA;
        } else { // Text columns (Assignment ID, Name)
            return ascending ? 
                cellA.localeCompare(cellB) : 
                cellB.localeCompare(cellA);
        }
    });
    
    // Clear tbody and append sorted rows
    tbody.innerHTML = '';
    rows.forEach(row => tbody.appendChild(row));
}

// Default sort by Assignment ID on page load
document.addEventListener('DOMContentLoaded', function() {
    sortTable(0);
});
