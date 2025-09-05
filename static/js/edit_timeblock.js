/**
 * Edit Time Block JavaScript
 * Handles oncall type toggling and assignment management for editing time blocks
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

// Global function for selecting entities - directly adds assignment
function selectEntity(entityId) {
    console.log('selectEntity called with:', entityId);
    
    const assignmentType = document.getElementById('assignment_type');
    
    if (!assignmentType || !assignmentType.value) {
        alert('Please select an assignment type first.');
        return;
    }
    
    // Check for duplicates
    const duplicate = assignments.find(a => 
        a.type === assignmentType.value && a.entity_id === entityId
    );
    if (duplicate) {
        alert('This assignment already exists.');
        return;
    }
    
    // Add assignment directly
    const assignment = {
        type: assignmentType.value,
        entity_id: entityId,
        notes: '', // Shortcuts don't have notes
        id: Date.now()
    };
    
    assignments.push(assignment);
    
    // Update UI
    renderAssignments();
    updateHiddenField();
    
    console.log('Added assignment from shortcut:', assignment);
}

// Function to show/hide sections based on assignment type
function updateVisibleSections() {
    const assignmentType = document.getElementById('assignment_type');
    const selectedType = assignmentType ? assignmentType.value : '';
    
    // Get sections
    const recentDonors = document.getElementById('recent-donors');
    const recentRecipients = document.getElementById('recent-recipients');
    const recentLabTasks = document.getElementById('recent-lab-tasks');
    
    // Hide all sections
    if (recentDonors) recentDonors.style.display = 'none';
    if (recentRecipients) recentRecipients.style.display = 'none';
    if (recentLabTasks) recentLabTasks.style.display = 'none';
    
    // Show appropriate section
    if (selectedType === 'donor' && recentDonors) {
        recentDonors.style.display = 'block';
    } else if (selectedType === 'recipient' && recentRecipients) {
        recentRecipients.style.display = 'block';
    } else if (selectedType === 'lab_task' && recentLabTasks) {
        recentLabTasks.style.display = 'block';
    }
}

// Function to add assignment to the list
function addAssignment() {
    const assignmentType = document.getElementById('assignment_type');
    const entityId = document.getElementById('entity_id');
    const notes = document.getElementById('id_assignment_notes');
    
    if (!assignmentType.value || !entityId.value.trim()) {
        alert('Please select an assignment type and enter an entity ID.');
        return;
    }
    
    // Check for duplicates
    const duplicate = assignments.find(a => 
        a.type === assignmentType.value && a.entity_id === entityId.value.trim()
    );
    if (duplicate) {
        alert('This assignment already exists.');
        return;
    }
    
    // Add to assignments array
    const assignment = {
        type: assignmentType.value,
        entity_id: entityId.value.trim(),
        notes: notes ? notes.value.trim() : '',
        id: Date.now()
    };
    
    assignments.push(assignment);
    
    // Clear form fields
    entityId.value = '';
    if (notes) notes.value = '';
    
    // Update UI
    renderAssignments();
    updateHiddenField();
}

// Function to remove assignment
function removeAssignment(id) {
    assignments = assignments.filter(a => a.id !== id);
    renderAssignments();
    updateHiddenField();
}

// Function to render assignments list
function renderAssignments() {
    console.log('renderAssignments called with', assignments.length, 'assignments');
    
    const assignmentsList = document.getElementById('assignments-list');
    const noAssignments = document.getElementById('no-assignments');
    
    console.log('DOM elements found:', {
        assignmentsList: !!assignmentsList,
        noAssignments: !!noAssignments
    });
    
    if (assignments.length === 0) {
        console.log('No assignments to display');
        if (noAssignments) {
            noAssignments.style.display = 'block';
            console.log('Showing no-assignments message');
        }
        // Hide any existing assignment items
        if (assignmentsList) {
            const existingItems = assignmentsList.querySelectorAll('.assignment-item');
            existingItems.forEach(item => item.remove());
        }
        return;
    }
    
    console.log('Displaying', assignments.length, 'assignments');
    if (noAssignments) {
        noAssignments.style.display = 'none';
        console.log('Hiding no-assignments message');
    }
    
    // Remove existing assignment items
    if (assignmentsList) {
        const existingItems = assignmentsList.querySelectorAll('.assignment-item');
        console.log('Removing', existingItems.length, 'existing items');
        existingItems.forEach(item => item.remove());
    }
    
    // Add each assignment
    assignments.forEach((assignment, index) => {
        console.log(`Creating assignment ${index}:`, assignment);
        
        const assignmentDiv = document.createElement('div');
        assignmentDiv.className = 'assignment-item d-flex justify-content-between align-items-center mb-2 p-2 border rounded bg-white';
        
        const typeColors = {
            'donor': 'success',
            'recipient': 'info', 
            'lab_task': 'warning'
        };
        
        const typeLabels = {
            'donor': 'Donor',
            'recipient': 'Recipient',
            'lab_task': 'Lab Task'
        };
        
        assignmentDiv.innerHTML = `
            <div>
                <span class="badge bg-${typeColors[assignment.type]} me-2">${typeLabels[assignment.type]}</span>
                <strong>${assignment.entity_id}</strong>
                ${assignment.notes ? `<br><small class="text-muted">${assignment.notes}</small>` : ''}
            </div>
            <button type="button" class="btn btn-outline-danger btn-sm" onclick="removeAssignment(${assignment.id})">
                <i class="bi bi-x"></i>
            </button>
        `;
        
        if (assignmentsList) {
            assignmentsList.appendChild(assignmentDiv);
            console.log('Added assignment div to DOM');
        } else {
            console.error('assignmentsList not found, cannot append assignment');
        }
    });
    
    console.log('renderAssignments completed');
}

// Function to update hidden field with assignments data
function updateHiddenField() {
    const hiddenField = document.getElementById('assignments-data');
    const jsonData = JSON.stringify(assignments);
    hiddenField.value = jsonData;
}

// Initialization function that will be called from the template with data
function initializeEditTimeblock(existingAssignments = []) {
    // Initialize assignments with existing data
    window.assignments = existingAssignments;
    
    console.log('DOM ready - initializing assignment management for edit');
    console.log('Loaded', assignments.length, 'existing assignments');
    
    const assignmentType = document.getElementById('assignment_type');
    const addBtn = document.getElementById('add-assignment-btn');
    
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
    
    if (assignmentType) {
        // Add event listener for dropdown changes
        assignmentType.addEventListener('change', function(e) {
            updateVisibleSections();
        });
    }
    
    if (addBtn) {
        // Add event listener for add button
        addBtn.addEventListener('click', function(e) {
            addAssignment();
        });
    }
    
    // Initial setup
    updateVisibleSections();
    
    // Force render existing assignments
    console.log('About to render assignments:', assignments.length);
    renderAssignments();
    updateHiddenField(); // Make sure hidden field has the existing data
    
    console.log('Assignment management initialized with', assignments.length, 'existing assignments');
}
