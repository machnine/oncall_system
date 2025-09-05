/**
 * Add Time Block JavaScript
 * Uses AssignmentManager utility for assignment management functionality
 */

// Global assignment manager instance
let assignmentManager;

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM ready - initializing assignment management');
    
    // Initialize AssignmentManager
    assignmentManager = new AssignmentManager({
        enableLogging: false  // Disable debug logging
    });
    
    // Make globally accessible for onclick handlers
    window.assignmentManager = assignmentManager;
    
    // Initialize the manager
    assignmentManager.init();
    
    console.log('Assignment management initialized');
});
