/**
 * Rota Calendar Initialization
 * This file contains the initialization logic for the rota calendar
 */

// Global initialization function
window.initializeRotaCalendar = function(availableStaff, staffBySeniority, csrfToken) {
    document.addEventListener('DOMContentLoaded', function() {
        if (window.initRotaCalendar) {
            window.initRotaCalendar(availableStaff, csrfToken, staffBySeniority);
        } else {
            console.error('RotaCalendar not found. Make sure rota_calendar.js is loaded first.');
        }
    });
};
