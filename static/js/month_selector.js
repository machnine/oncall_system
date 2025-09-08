/**
 * Month Selector Component JavaScript
 * Handles month/year validation and form controls
 */

DOMUtils.ready(function() {
    const monthSelect = DOMUtils.safeGetById('monthSelect');
    const yearSelect = DOMUtils.safeGetById('yearSelect');
    
    if (!monthSelect || !yearSelect) return;
    
    function updateMonthOptions() {
        const selectedYear = parseInt(yearSelect.value);
        const currentDate = new Date();
        const currentYear = currentDate.getFullYear();
        const currentMonth = currentDate.getMonth() + 1; // JavaScript months are 0-based
        
        // Enable/disable month options based on selected year
        for (let i = 1; i <= 12; i++) {
            const option = monthSelect.querySelector(`option[value="${i}"]`);
            if (option) {
                if (selectedYear > currentYear || (selectedYear === currentYear && i > currentMonth)) {
                    option.disabled = true;
                    option.style.color = '#ccc';
                } else {
                    option.disabled = false;
                    option.style.color = '';
                }
            }
        }
        
        // If current selection is disabled, reset to current month
        const selectedMonth = parseInt(monthSelect.value);
        if (selectedYear > currentYear || (selectedYear === currentYear && selectedMonth > currentMonth)) {
            monthSelect.value = currentMonth;
        }
    }
    
    // Update month options when year changes
    yearSelect.addEventListener('change', updateMonthOptions);
    
    // Initial update
    updateMonthOptions();
});