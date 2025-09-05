/**
 * Edit Time Block JavaScript
 * Handles oncall type toggling and uses AssignmentManager utility for assignment management
 */

// OnCall Type functionality - disable claim field for NHSP
let previousOncallType = null;

function toggleClaimField(showPrompt = true) {
    const oncallTypeInputs = document.querySelectorAll('input[name="oncall_type"]');
    const claimField = document.querySelector('input[name="claim"]');
    const claimButtons = document.querySelectorAll('button[onclick^="setClaimHours"]');
    const claimContainer = claimField.closest('.mb-3');
    
    let currentOncallType = null;
    oncallTypeInputs.forEach(input => {
        if (input.checked) {
            currentOncallType = input.value;
        }
    });
    
    // Check if switching from Normal to NHSP with existing claim hours
    if (showPrompt && previousOncallType === 'normal' && currentOncallType === 'nhsp' && claimField.value.trim() !== '') {
        const confirmClear = confirm(
            'Switching to NHSP will clear the current claim hours (' + claimField.value + ').\n\n' +
            'NHSP blocks are claimed differently outside of this system.\n\n' +
            'Do you want to continue?'
        );
        
        if (!confirmClear) {
            // User cancelled - revert to previous selection
            oncallTypeInputs.forEach(input => {
                if (input.value === previousOncallType) {
                    input.checked = true;
                } else {
                    input.checked = false;
                }
            });
            return; // Exit without making changes
        }
    }
    
    // Update the previous type for next time
    previousOncallType = currentOncallType;
    
    if (currentOncallType === 'nhsp') {
        // Disable claim field and buttons for NHSP
        claimField.disabled = true;
        claimField.value = '';
        claimField.style.backgroundColor = '#f8f9fa';
        claimButtons.forEach(btn => {
            btn.disabled = true;
            btn.classList.add('disabled');
        });
        // Add visual indication
        if (claimContainer) {
            claimContainer.style.opacity = '0.6';
        }
    } else {
        // Enable claim field and buttons for Normal
        claimField.disabled = false;
        claimField.style.backgroundColor = '';
        claimButtons.forEach(btn => {
            btn.disabled = false;
            btn.classList.remove('disabled');
        });
        // Remove visual indication
        if (claimContainer) {
            claimContainer.style.opacity = '1';
        }
    }
}

// Claim hours functionality
function setClaimHours(hours) {
    const claimField = document.querySelector('input[name="claim"]');
    if (claimField && !claimField.disabled) {
        claimField.value = hours;
        claimField.focus();
    }
}

// Global assignment manager instance
let assignmentManager;

// Initialization function that will be called from the template with data
function initializeEditTimeblock(existingAssignments = []) {
    console.log('DOM ready - initializing assignment management for edit');
    console.log('Loaded', existingAssignments.length, 'existing assignments');
    
    // Initialize AssignmentManager with existing assignments
    assignmentManager = new AssignmentManager({
        initialAssignments: existingAssignments,
        enableLogging: false  // Disable debug logging
    });
    
    // Make globally accessible for onclick handlers
    window.assignmentManager = assignmentManager;
    
    // Initialize oncall type functionality
    const oncallTypeInputs = document.querySelectorAll('input[name="oncall_type"]');
    oncallTypeInputs.forEach(input => {
        if (input.checked) {
            previousOncallType = input.value;
        }
    });
    toggleClaimField(false); // Don't show prompt on initial load
    
    // Add event listeners to oncall type radio buttons
    oncallTypeInputs.forEach(input => {
        input.addEventListener('change', function() {
            toggleClaimField(true); // Show prompt for user changes
        });
    });
    
    // Initialize the assignment manager
    assignmentManager.init();
    
    console.log('Assignment management initialized with', existingAssignments.length, 'existing assignments');
}
