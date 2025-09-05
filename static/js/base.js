/**
 * Base JavaScript functionality
 * Common scripts used across the application
 */

// Auto-dismiss alerts after 3 seconds with smooth fade
document.addEventListener('DOMContentLoaded', function() {
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            // Add smooth fade-out transition
            alert.style.transition = 'opacity 0.8s ease-out';
            alert.style.opacity = '0';
            
            // Remove element after fade completes
            setTimeout(function() {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }, 800);
        }, 3000);
    });
});
