/**
 * Assignment Management Utility
 * Reusable assignment functionality for time block forms
 */

class AssignmentManager {
    constructor(options = {}) {
        this.assignments = options.initialAssignments || [];
        this.typeColors = {
            'donor': 'success',
            'recipient': 'info', 
            'lab_task': 'warning'
        };
        this.typeLabels = {
            'donor': 'Donor',
            'recipient': 'Recipient',
            'lab_task': 'Lab Task'
        };
        
        // DOM element IDs (can be customized)
        this.elements = {
            assignmentType: options.assignmentTypeId || 'assignment_type',
            entityId: options.entityIdId || 'entity_id',
            notes: options.notesId || 'id_assignment_notes',
            addButton: options.addButtonId || 'add-assignment-btn',
            assignmentsList: options.assignmentsListId || 'assignments-list',
            noAssignments: options.noAssignmentsId || 'no-assignments',
            hiddenField: options.hiddenFieldId || 'assignments-data',
            recentDonors: options.recentDonorsId || 'recent-donors',
            recentRecipients: options.recentRecipientsId || 'recent-recipients',
            recentLabTasks: options.recentLabTasksId || 'recent-lab-tasks'
        };
        
        this.onAssignmentChange = options.onAssignmentChange || (() => {});
        this.enableLogging = options.enableLogging || false;
    }

    /**
     * Initialize the assignment manager
     */
    init() {
        this.log('Initializing assignment management');
        
        const assignmentType = document.getElementById(this.elements.assignmentType);
        const addBtn = document.getElementById(this.elements.addButton);
        
        if (assignmentType) {
            assignmentType.addEventListener('change', (e) => {
                this.updateVisibleSections();
            });
        }
        
        if (addBtn) {
            addBtn.addEventListener('click', (e) => {
                this.addAssignment();
            });
        }
        
        // Initial setup
        this.updateVisibleSections();
        this.renderAssignments();
        this.updateHiddenField();
        
        this.log('Assignment management initialized with', this.assignments.length, 'assignments');
    }

    /**
     * Add assignment from entity selection (shortcuts)
     * @param {string} entityId - The entity ID to add
     */
    selectEntity(entityId) {
        this.log('selectEntity called with:', entityId);
        
        const assignmentType = document.getElementById(this.elements.assignmentType);
        
        if (!assignmentType || !assignmentType.value) {
            alert('Please select an assignment type first.');
            return;
        }
        
        // Check for duplicates
        const duplicate = this.assignments.find(a => 
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
        
        this.assignments.push(assignment);
        
        // Update UI
        this.renderAssignments();
        this.updateHiddenField();
        this.onAssignmentChange(this.assignments);
        
        this.log('Added assignment from shortcut:', assignment);
    }

    /**
     * Show/hide sections based on assignment type
     */
    updateVisibleSections() {
        const assignmentType = document.getElementById(this.elements.assignmentType);
        const selectedType = assignmentType ? assignmentType.value : '';
        
        // Get sections
        const recentDonors = document.getElementById(this.elements.recentDonors);
        const recentRecipients = document.getElementById(this.elements.recentRecipients);
        const recentLabTasks = document.getElementById(this.elements.recentLabTasks);
        
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

    /**
     * Add assignment from form
     */
    addAssignment() {
        this.log('addAssignment function called');
        
        const assignmentType = document.getElementById(this.elements.assignmentType);
        const entityId = document.getElementById(this.elements.entityId);
        const notes = document.getElementById(this.elements.notes);
        
        if (!assignmentType || !entityId || !assignmentType.value || !entityId.value.trim()) {
            alert('Please select an assignment type and enter an entity ID.');
            return;
        }
        
        // Check for duplicates
        const duplicate = this.assignments.find(a => 
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
        
        this.log('Adding assignment:', assignment);
        this.assignments.push(assignment);
        
        // Clear form fields
        entityId.value = '';
        if (notes) notes.value = '';
        
        // Update UI
        this.renderAssignments();
        this.updateHiddenField();
        this.onAssignmentChange(this.assignments);
        
        this.log('Assignment added successfully');
    }

    /**
     * Remove assignment
     * @param {number} id - Assignment ID to remove
     */
    removeAssignment(id) {
        this.assignments = this.assignments.filter(a => a.id !== id);
        this.renderAssignments();
        this.updateHiddenField();
        this.onAssignmentChange(this.assignments);
        this.log('Removed assignment with id:', id);
    }

    /**
     * Render assignments list in the DOM
     */
    renderAssignments() {
        this.log('renderAssignments called with', this.assignments.length, 'assignments');
        
        const assignmentsList = document.getElementById(this.elements.assignmentsList);
        const noAssignments = document.getElementById(this.elements.noAssignments);
        
        if (this.assignments.length === 0) {
            this.log('No assignments to display');
            if (noAssignments) noAssignments.style.display = 'block';
            // Hide any existing assignment items
            if (assignmentsList) {
                const existingItems = assignmentsList.querySelectorAll('.assignment-item');
                existingItems.forEach(item => item.remove());
            }
            return;
        }
        
        this.log('Displaying', this.assignments.length, 'assignments');
        if (noAssignments) noAssignments.style.display = 'none';
        
        // Remove existing assignment items
        if (assignmentsList) {
            const existingItems = assignmentsList.querySelectorAll('.assignment-item');
            existingItems.forEach(item => item.remove());
        }
        
        // Add each assignment
        this.assignments.forEach((assignment, index) => {
            this.log(`Rendering assignment ${index}:`, assignment);
            
            const assignmentDiv = document.createElement('div');
            assignmentDiv.className = 'assignment-item d-flex justify-content-between align-items-center mb-2 p-2 border rounded bg-white';
            
            assignmentDiv.innerHTML = `
                <div>
                    <span class="badge bg-${this.typeColors[assignment.type]} me-2">${this.typeLabels[assignment.type]}</span>
                    <strong>${assignment.entity_id}</strong>
                    ${assignment.notes ? `<br><small class="text-muted">${assignment.notes}</small>` : ''}
                </div>
                <button type="button" class="btn btn-outline-danger btn-sm" onclick="window.assignmentManager.removeAssignment(${assignment.id})">
                    <i class="bi bi-x"></i>
                </button>
            `;
            
            if (assignmentsList) {
                assignmentsList.appendChild(assignmentDiv);
                this.log('Added assignment div to DOM');
            } else {
                console.error('assignmentsList not found, cannot append assignment');
            }
        });
        
        this.log('renderAssignments completed');
    }

    /**
     * Update hidden field with assignments data for form submission
     */
    updateHiddenField() {
        const hiddenField = document.getElementById(this.elements.hiddenField);
        if (hiddenField) {
            const jsonData = JSON.stringify(this.assignments);
            hiddenField.value = jsonData;
            this.log('Updated hidden field with:', jsonData);
        }
    }

    /**
     * Set assignments (for initialization with existing data)
     * @param {Array} assignments - Array of assignment objects
     */
    setAssignments(assignments) {
        this.assignments = assignments || [];
        this.renderAssignments();
        this.updateHiddenField();
        this.onAssignmentChange(this.assignments);
    }

    /**
     * Get current assignments
     * @returns {Array} Current assignments array
     */
    getAssignments() {
        return this.assignments;
    }

    /**
     * Log helper (only logs if logging is enabled)
     */
    log(...args) {
        if (this.enableLogging) {
            console.log(...args);
        }
    }
}

// Global function for backwards compatibility with onclick handlers
window.selectEntity = function(entityId) {
    if (window.assignmentManager) {
        window.assignmentManager.selectEntity(entityId);
    } else {
        console.error('Assignment manager not initialized');
    }
};

// Export for use in other modules
window.AssignmentManager = AssignmentManager;
