/**
 * Signoff Management Table Sorting
 * Handles table sorting functionality for the monthly claim management page
 */

let sortDirection = {};

function sortTable(columnIndex) {
    const table = document.getElementById('signoffTable');
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
        let cellA, cellB;
        
        if (columnIndex === 0) { // Staff column - sort by assignment ID
            cellA = a.cells[columnIndex].querySelector('strong').textContent.trim();
            cellB = b.cells[columnIndex].querySelector('strong').textContent.trim();
        } else if (columnIndex === 1) { // Time Blocks column - extract number from badge
            cellA = parseInt(a.cells[columnIndex].querySelector('.badge').textContent.match(/\d+/)[0]);
            cellB = parseInt(b.cells[columnIndex].querySelector('.badge').textContent.match(/\d+/)[0]);
        } else if (columnIndex === 2 || columnIndex === 3) { // Hours/Claims columns - numeric
            cellA = parseFloat(a.cells[columnIndex].textContent.replace('h', '').trim()) || 0;
            cellB = parseFloat(b.cells[columnIndex].textContent.replace('h', '').trim()) || 0;
        } else if (columnIndex === 4) { // Status column - sort by badge text
            cellA = a.cells[columnIndex].querySelector('.badge').textContent.trim();
            cellB = b.cells[columnIndex].querySelector('.badge').textContent.trim();
        } else {
            cellA = a.cells[columnIndex].textContent.trim();
            cellB = b.cells[columnIndex].textContent.trim();
        }
        
        // Numeric comparison for numeric columns
        if (columnIndex === 1 || columnIndex === 2 || columnIndex === 3) {
            return ascending ? cellA - cellB : cellB - cellA;
        } else { // Text comparison for other columns
            return ascending ? 
                cellA.localeCompare(cellB) : 
                cellB.localeCompare(cellA);
        }
    });
    
    // Clear tbody and append sorted rows
    tbody.innerHTML = '';
    rows.forEach(row => tbody.appendChild(row));
}

// Default sort by Staff ID on page load
document.addEventListener('DOMContentLoaded', function() {
    sortTable(0);
});
