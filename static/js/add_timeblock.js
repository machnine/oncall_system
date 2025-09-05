/**
 * Add Time Block JavaScript
 * Handles assignment management functionality for adding time blocks
 */

console.log('JavaScript loading...');

// Array to store current assignments
let assignments = [];

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
    console.log('addAssignment function called');
    
    const assignmentType = document.getElementById('assignment_type');
    const entityId = document.getElementById('entity_id');
    const notes = document.getElementById('id_assignment_notes');
    
    console.log('Form elements:', {
        assignmentType: assignmentType,
        entityId: entityId,
        notes: notes
    });
    
    console.log('Form values:', {
        assignmentType: assignmentType ? assignmentType.value : 'null',
        entityId: entityId ? entityId.value : 'null',
        notes: notes ? notes.value : 'null'
    });
    
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
        id: Date.now() // Simple unique ID for removal
    };
    
    console.log('Adding assignment:', assignment);
    assignments.push(assignment);
    console.log('Assignments array now:', assignments);
    
    // Clear form fields
    entityId.value = '';
    if (notes) notes.value = '';
    
    // Update UI
    console.log('Calling renderAssignments');
    renderAssignments();
    updateHiddenField();
    
    console.log('Assignment added successfully');
}

// Function to remove assignment
function removeAssignment(id) {
    assignments = assignments.filter(a => a.id !== id);
    renderAssignments();
    updateHiddenField();
    console.log('Removed assignment with id:', id);
}

// Function to render assignments list
function renderAssignments() {
    console.log('renderAssignments called, assignments:', assignments);
    
    const assignmentsList = document.getElementById('assignments-list');
    const noAssignments = document.getElementById('no-assignments');
    
    console.log('DOM elements:', {
        assignmentsList: assignmentsList,
        noAssignments: noAssignments
    });
    
    if (assignments.length === 0) {
        console.log('No assignments, showing placeholder');
        if (noAssignments) noAssignments.style.display = 'block';
        // Hide any existing assignment items
        if (assignmentsList) {
            const existingItems = assignmentsList.querySelectorAll('.assignment-item');
            existingItems.forEach(item => item.remove());
        }
        return;
    }
    
    console.log('Has assignments, hiding placeholder');
    if (noAssignments) noAssignments.style.display = 'none';
    
    // Remove existing assignment items
    if (assignmentsList) {
        const existingItems = assignmentsList.querySelectorAll('.assignment-item');
        console.log('Removing existing items:', existingItems.length);
        existingItems.forEach(item => item.remove());
    }
    
    // Add each assignment
    assignments.forEach((assignment, index) => {
        console.log(`Rendering assignment ${index}:`, assignment);
        
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
            console.log('Assignment div added to DOM');
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
    console.log('Updated hidden field with:', jsonData);
}

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM ready - initializing assignment management');
    
    const assignmentType = document.getElementById('assignment_type');
    const addBtn = document.getElementById('add-assignment-btn');
    
    console.log('Assignment type dropdown:', assignmentType);
    console.log('Add button:', addBtn);
    
    if (assignmentType) {
        // Add event listener for dropdown changes
        assignmentType.addEventListener('change', function(e) {
            console.log('Dropdown changed to:', e.target.value);
            updateVisibleSections();
        });
    }
    
    if (addBtn) {
        // Add event listener for add button
        addBtn.addEventListener('click', function(e) {
            console.log('Add button clicked');
            addAssignment();
        });
        console.log('Add button event listener attached');
    } else {
        console.error('Add button not found!');
    }
    
    // Initial setup
    updateVisibleSections();
    renderAssignments();
    
    console.log('Assignment management initialized');
});
