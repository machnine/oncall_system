/**
 * Bank Holiday Detail Page JavaScript
 * Handles year expansion/collapse and holiday view toggling
 */

// Store year data for JavaScript access - will be populated by template
let yearData = {};

// Master expand/collapse all years
function toggleAllYears() {
    const masterBtn = document.getElementById('masterToggleBtn');
    const isExpandAction = masterBtn.innerHTML.includes('Expand All');
    
    Object.keys(yearData).forEach(year => {
        const yearBody = document.getElementById('yearBody' + year);
        const yearToggleBtn = document.getElementById('yearToggleBtn' + year);
        
        if (isExpandAction) {
            // Expand all
            yearBody.classList.add('show');
            yearToggleBtn.innerHTML = '<i class="bi bi-caret-up"></i>';
            document.getElementById('toggleBtn' + year).style.display = 'inline-block';
        } else {
            // Collapse all
            yearBody.classList.remove('show');
            yearToggleBtn.innerHTML = '<i class="bi bi-caret-down"></i>';
            document.getElementById('toggleBtn' + year).style.display = 'none';
            // Reset holiday view to important holidays
            resetHolidayView(year);
        }
    });
    
    if (isExpandAction) {
        masterBtn.innerHTML = '<i class="bi bi-caret-up"></i> Collapse All';
    } else {
        masterBtn.innerHTML = '<i class="bi bi-caret-down"></i> Expand All';
    }
}

// Individual year expand/collapse
function toggleYear(year) {
    const yearBody = document.getElementById('yearBody' + year);
    const yearToggleBtn = document.getElementById('yearToggleBtn' + year);
    const holidayToggleBtn = document.getElementById('toggleBtn' + year);
    
    if (yearBody.classList.contains('show')) {
        // Collapse year
        yearBody.classList.remove('show');
        yearToggleBtn.innerHTML = '<i class="bi bi-caret-down"></i>';
        holidayToggleBtn.style.display = 'none';
        // Reset holiday view to important holidays
        resetHolidayView(year);
    } else {
        // Expand year
        yearBody.classList.add('show');
        yearToggleBtn.innerHTML = '<i class="bi bi-caret-up"></i>';
        holidayToggleBtn.style.display = 'inline-block';
    }
    
    // Update master button state
    updateMasterButtonState();
}

// Holiday view toggle (important vs all)
function toggleHolidays(year) {
    const importantTable = document.getElementById('importantTable' + year);
    const allTable = document.getElementById('allTable' + year);
    const toggleBtn = document.getElementById('toggleBtn' + year);
    
    if (allTable.style.display === 'none') {
        // Show all holidays
        importantTable.style.display = 'none';
        allTable.style.display = 'block';
        toggleBtn.innerHTML = '<i class="bi bi-caret-up"></i> Key days only';
    } else {
        // Show important holidays only
        allTable.style.display = 'none';
        importantTable.style.display = 'block';
        toggleBtn.innerHTML = '<i class="bi bi-caret-down"></i> Show all days';
    }
}

// Reset holiday view to important holidays only
function resetHolidayView(year) {
    const importantTable = document.getElementById('importantTable' + year);
    const allTable = document.getElementById('allTable' + year);
    const toggleBtn = document.getElementById('toggleBtn' + year);
    
    allTable.style.display = 'none';
    importantTable.style.display = 'block';
    toggleBtn.innerHTML = '<i class="bi bi-caret-down"></i> Show all days';
}

// Update master button state based on individual year states
function updateMasterButtonState() {
    const masterBtn = document.getElementById('masterToggleBtn');
    const allCollapsed = document.querySelectorAll('.card-body.collapse:not(.show)').length > 0;
    
    if (allCollapsed) {
        masterBtn.innerHTML = '<i class="bi bi-caret-down"></i> Expand All';
    } else {
        masterBtn.innerHTML = '<i class="bi bi-caret-up"></i> Collapse All';
    }
}

// Function to set year data from template
function setYearData(data) {
    yearData = data;
}