/**
 * Rota Calendar JavaScript
 * Handles context menu, staff assignment, and day management functionality
 */

class RotaCalendar {
    constructor(availableStaff, csrfToken, staffBySeniority = null) {
        this.availableStaff = availableStaff;
        this.staffBySeniority = staffBySeniority || this.groupStaffBySeniority(availableStaff);
        this.csrfToken = csrfToken;
        this.currentDay = null;
        this.currentSeniorityLevel = null;
        this.currentSeniorityName = null;
        this.contextMenu = document.getElementById('contextMenu');
        
        this.init();
    }

    // Group staff by seniority level if not provided
    groupStaffBySeniority(staff) {
        const grouped = {
            'trainee': [],
            'oncall': [],
            'senior': []
        };
        
        staff.forEach(member => {
            if (grouped[member.seniority_level]) {
                grouped[member.seniority_level].push(member);
            }
        });
        
        return grouped;
    }

    init() {
        // Initialize Bootstrap tooltips
        this.initTooltips();
        
        // Setup event handlers
        this.attachRotaRowEventHandlers();
        this.attachDayEventHandlers();
        this.attachContextMenuHandlers();
        this.attachDocumentHandlers();
        
        // Attach delete functionality to existing staff entries
        this.attachStaffDeleteHandlers();
    }

    initTooltips() {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    attachRotaRowEventHandlers() {
        document.querySelectorAll('.rota-row').forEach(rotaRow => {
            // Remove existing event listener to avoid duplicates
            rotaRow.removeEventListener('contextmenu', this.rotaRowContextHandler.bind(this));
            // Attach new event listener
            rotaRow.addEventListener('contextmenu', this.rotaRowContextHandler.bind(this));
        });
    }

    rotaRowContextHandler(e) {
        e.preventDefault();
        e.stopPropagation(); // Prevent event from bubbling to day cell
        
        this.currentDay = e.target.closest('.rota-day');
        this.currentSeniorityLevel = e.target.closest('.rota-row').dataset.seniority;
        this.currentSeniorityName = e.target.closest('.rota-row').dataset.seniorityName;
        
        this.showContextMenu(e.pageX, e.pageY);
    }

    attachDayEventHandlers() {
        document.querySelectorAll('.rota-day').forEach(dayCell => {
            dayCell.addEventListener('contextmenu', (e) => {
                // Only handle if not clicking on a rota-row
                if (!e.target.closest('.rota-row')) {
                    e.preventDefault();
                    this.currentDay = dayCell;
                    this.currentSeniorityLevel = null;
                    this.currentSeniorityName = 'Day';
                    
                    this.showContextMenu(e.pageX, e.pageY);
                }
            });
        });
    }

    showContextMenu(x, y) {
        // Position the context menu
        const rect = this.contextMenu.getBoundingClientRect();
        
        // Prevent menu from going off-screen
        if (x + rect.width > window.innerWidth) {
            x = window.innerWidth - rect.width - 10;
        }
        if (y + rect.height > window.innerHeight) {
            y = window.innerHeight - rect.height - 10;
        }
        
        this.contextMenu.style.left = x + 'px';
        this.contextMenu.style.top = y + 'px';
        this.contextMenu.style.display = 'block';
        
        this.updateContextMenu();
    }

    attachContextMenuHandlers() {
        // Shift type toggle
        document.getElementById('toggle-shift-type').addEventListener('click', (e) => {
            e.preventDefault();
            this.toggleShiftType();
        });

        // Clear day
        document.getElementById('clear-day').addEventListener('click', (e) => {
            e.preventDefault();
            this.clearDay();
        });
    }

    attachDocumentHandlers() {
        // Hide context menu when clicking elsewhere
        document.addEventListener('click', (e) => {
            if (!this.contextMenu.contains(e.target)) {
                this.contextMenu.style.display = 'none';
            }
        });
    }

    attachStaffDeleteHandlers() {
        // Attach hover and click events to all existing staff entries
        document.querySelectorAll('.staff-entry').forEach(staffSpan => {
            this.attachStaffDeleteEvents(staffSpan);
        });
    }

    attachStaffDeleteEvents(staffSpan) {
        // Check if delete button already exists
        let deleteBtn = staffSpan.querySelector('.staff-delete-btn');
        
        // If no delete button exists, create one
        if (!deleteBtn) {
            deleteBtn = document.createElement('i');
            deleteBtn.className = 'bi bi-x-circle-fill staff-delete-btn';
            deleteBtn.style.cssText = `
                position: absolute;
                top: -8px;
                right: -8px;
                font-size: 1rem;
                color: #dc3545;
                cursor: pointer;
                opacity: 0;
                transition: opacity 0.2s ease;
                z-index: 20;
                text-shadow: 1px 1px 2px rgba(255,255,255,0.9), -1px -1px 2px rgba(255,255,255,0.9);
                filter: drop-shadow(0 0 2px rgba(255,255,255,0.8));
            `;
            deleteBtn.title = 'Remove staff from rota';
            staffSpan.appendChild(deleteBtn);
        }

        // Add hover events to show/hide delete button
        staffSpan.addEventListener('mouseenter', () => {
            deleteBtn.style.opacity = '1';
        });
        
        staffSpan.addEventListener('mouseleave', () => {
            deleteBtn.style.opacity = '0';
        });
        
        // Add click event to delete button (remove existing listeners first)
        const newDeleteBtn = deleteBtn.cloneNode(true);
        deleteBtn.parentNode.replaceChild(newDeleteBtn, deleteBtn);
        
        newDeleteBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            const shiftId = staffSpan.dataset.shiftId;
            this.removeStaffFromRota(shiftId, staffSpan);
        });
    }

    updateContextMenu() {
        const shiftType = this.currentDay.dataset.shiftType;
        const shiftTypeToggle = document.getElementById('toggle-shift-type');
        const shiftTypeText = document.getElementById('shift-type-text');
        const seniorityNameSpan = document.getElementById('seniority-name');
        
        // Update seniority name in header
        seniorityNameSpan.textContent = this.currentSeniorityName;
        
        // Update shift type toggle text
        if (shiftType === 'nhsp') {
            shiftTypeText.textContent = 'Remove NHSP';
        } else {
            shiftTypeText.textContent = 'Set NHSP';
        }
        
        // Populate staff list for the specific seniority level
        this.populateStaffList();
    }

    populateStaffList() {
        const container = document.getElementById('staff-list');
        container.innerHTML = '';
        
        // If no specific seniority level selected, show seniority level selection first
        if (!this.currentSeniorityLevel) {
            this.showSenioritySelection(container);
            return;
        }
        
        this.showStaffForSeniority(container);
    }

    showSenioritySelection(container) {
        const seniorityLevels = [
            { level: 'trainee', name: 'Trainee' },
            { level: 'oncall', name: 'On-Call' },
            { level: 'senior', name: 'Senior' }
        ];
        
        seniorityLevels.forEach(seniority => {
            const seniorityItem = document.createElement('a');
            seniorityItem.className = 'dropdown-item';
            seniorityItem.href = '#';
            seniorityItem.innerHTML = `<i class="bi bi-people"></i> Add ${seniority.name} Staff`;
            
            seniorityItem.addEventListener('click', (e) => {
                e.preventDefault();
                this.handleSenioritySelection(seniority);
            });
            
            container.appendChild(seniorityItem);
        });
    }

    async handleSenioritySelection(seniority) {
        // Set the seniority level and show staff for that level
        this.currentSeniorityLevel = seniority.level;
        this.currentSeniorityName = seniority.name;
        
        console.log("Selected seniority level:", this.currentSeniorityLevel);
        
        // Check if this is an empty day that needs a RotaEntry created first
        const isEmpty = !this.currentDay.dataset.rotaEntryId || this.currentDay.dataset.rotaEntryId === '';
        
        if (isEmpty) {
            console.log('Empty day detected after seniority selection, creating RotaEntry first');
            try {
                await this.createRotaEntry();
                this.populateStaffList();
            } catch (error) {
                console.error('Error creating rota entry:', error);
                alert('An error occurred while creating rota entry');
            }
        } else {
            // RotaEntry already exists, just show staff list
            this.populateStaffList();
        }
    }

    showStaffForSeniority(container) {
        // Filter staff by current seniority level
        const staffToShow = this.currentSeniorityLevel && this.staffBySeniority[this.currentSeniorityLevel] 
            ? this.staffBySeniority[this.currentSeniorityLevel] 
            : [];
        
        if (staffToShow.length === 0) {
            const noStaffItem = document.createElement('div');
            noStaffItem.className = 'dropdown-item-text text-muted';
            noStaffItem.textContent = `No ${this.currentSeniorityName} staff available`;
            container.appendChild(noStaffItem);
            return;
        }
        
        staffToShow.forEach(staff => {
            const staffItem = document.createElement('a');
            staffItem.className = 'dropdown-item d-flex align-items-center';
            staffItem.href = '#';
            staffItem.innerHTML = `
                <div class="me-2" style="width: 12px; height: 12px; background-color: ${staff.color}70; border-radius: 2px;"></div>
                ${staff.assignment_id} - ${staff.name}
            `;
            
            staffItem.addEventListener('click', (e) => {
                e.preventDefault();
                this.addStaffToDay(staff);
            });
            
            container.appendChild(staffItem);
        });
    }

    async addStaffToDay(staff) {
        // By this point, currentSeniorityLevel should always be set
        if (!this.currentSeniorityLevel) {
            alert('Please select a seniority level first');
            return;
        }
        
        // Check if this is an empty day that needs a RotaEntry created first
        const isEmpty = !this.currentDay.dataset.rotaEntryId || this.currentDay.dataset.rotaEntryId === '';
        
        if (isEmpty) {
            // This should only happen if user directly clicked a staff member without going through seniority selection
            console.log('Empty day detected in addStaffToDay, creating RotaEntry first');
            try {
                await this.createRotaEntry();
                await this.performStaffAddition(staff);
            } catch (error) {
                console.error('Error in staff addition process:', error);
                alert('An error occurred while adding staff');
            }
        } else {
            console.log('RotaEntry already exists, adding staff directly');
            await this.performStaffAddition(staff);
        }
        
        this.contextMenu.style.display = 'none';
    }

    async createRotaEntry() {
        const rotaCreationData = {
            date: this.currentDay.dataset.date
        };

        const response = await fetch('/rota/create-entry/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.csrfToken
            },
            body: JSON.stringify(rotaCreationData)
        });

        const data = await response.json();

        if (data.success) {
            console.log('RotaEntry created:', data.rota_entry_id);
            // Update the day's attributes
            this.currentDay.dataset.rotaEntryId = data.rota_entry_id;
            this.currentDay.dataset.shiftType = data.shift_type;
            
            // Create DOM structure
            this.createRotaStructure();
        } else {
            throw new Error('Error creating rota entry: ' + data.error);
        }
    }

    createRotaStructure() {
        // Check if we already have a structured day with content area
        const existingContentArea = this.currentDay.querySelector('.px-1.pb-1');
        if (existingContentArea) {
            // Remove "No rota" indicator from the middle row
            const oncallRow = existingContentArea.querySelector('.rota-row[data-seniority="oncall"]');
            if (oncallRow) {
                const noRotaIndicator = oncallRow.querySelector('.text-muted');
                if (noRotaIndicator) {
                    noRotaIndicator.remove();
                }
                // Remove the centering classes since we'll be adding staff
                oncallRow.classList.remove('align-items-center', 'justify-content-center');
            }
            return; // Structure already exists, just cleaned up
        }
        
        // If we don't have the expected structure, this might be a completely empty day
        // In that case, we need to create the full day structure including header
        const hasHeader = this.currentDay.querySelector('.d-flex.justify-content-between');
        if (!hasHeader) {
            // Create the complete day structure for empty days
            this.currentDay.innerHTML = `
                <div class="position-relative h-100">
                    <!-- Date header with proper spacing for date and badges -->
                    <div class="d-flex justify-content-between align-items-start p-1">
                        <span class="fw-bold" style="font-size: 0.9rem;">
                            ${this.currentDay.dataset.date.split('-')[2]}
                        </span>
                        <div class="d-flex flex-wrap gap-1">
                        </div>
                    </div>
                    <div class="px-1 pb-1">
                        <div class="mb-1 d-flex flex-wrap rota-row" style="min-height: 1.5rem; gap: 1px; overflow: visible;" data-seniority="trainee" data-seniority-name="Trainee"></div>
                        <div class="mb-1 d-flex flex-wrap rota-row" style="min-height: 1.5rem; gap: 1px; overflow: visible;" data-seniority="oncall" data-seniority-name="On-Call"></div>
                        <div class="mb-1 d-flex flex-wrap rota-row" style="min-height: 1.5rem; gap: 1px; overflow: visible;" data-seniority="senior" data-seniority-name="Senior"></div>
                    </div>
                </div>
            `;
            this.attachRotaRowEventHandlers();
        }
    }

    async performStaffAddition(staff) {
        console.log('Performing staff addition for:', staff);
        const formData = {
            date: this.currentDay.dataset.date,
            staff_id: staff.id,
            seniority_level: this.currentSeniorityLevel
        };

        const response = await fetch('/rota/add-staff/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.csrfToken
            },
            body: JSON.stringify(formData)
        });

        const data = await response.json();

        if (data.success) {
            console.log('Staff addition response:', data);
            // Update the DOM with the new staff member
            this.updateDayDOM(data);
            console.log('Staff added successfully and DOM updated');
        } else {
            throw new Error('Error: ' + data.error);
        }
    }

    async toggleShiftType() {
        const formData = {
            date: this.currentDay.dataset.date
        };

        try {
            const response = await fetch('/rota/toggle-shift-type/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken
                },
                body: JSON.stringify(formData)
            });

            const data = await response.json();

            if (data.success) {
                // Update the day's shift type
                this.currentDay.dataset.shiftType = data.shift_type;
                this.currentDay.dataset.rotaEntryId = data.rota_entry_id;
                
                // If this was an empty day, create the rota structure
                this.createRotaStructure();
                
                // Update NHSP badge visibility
                this.updateNHSPBadge(this.currentDay, data.shift_type);
                console.log('Shift type toggled successfully');
            } else {
                alert('Error: ' + data.error);
            }
        } catch (error) {
            console.error('Error toggling shift type:', error);
            alert('An error occurred while toggling shift type');
        }
        
        this.contextMenu.style.display = 'none';
    }

    async removeStaffFromRota(shiftId, staffSpan) {
        if (confirm('Are you sure you want to remove this staff member from the rota?')) {
            try {
                const response = await fetch('/rota/remove-staff/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.csrfToken
                    },
                    body: JSON.stringify({
                        shift_id: shiftId
                    })
                });

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const data = await response.json();

                if (data.success) {
                    // Get the day cell before removing the staff span
                    const dayCell = staffSpan.closest('.rota-day');
                    
                    // Remove the staff span from DOM
                    staffSpan.remove();
                    
                    // Check if this was the last staff member in the day
                    const remainingStaffSpans = dayCell.querySelectorAll('.staff-entry');
                    
                    if (remainingStaffSpans.length === 0) {
                        // No staff left, show empty day indicator
                        this.clearDayDOM(dayCell);
                    }
                    
                    console.log('Staff removed successfully');
                } else {
                    console.error('Server error:', data.error);
                    alert('Error: ' + (data.error || 'Unknown server error'));
                }
            } catch (error) {
                console.error('Error removing staff:', error);
                alert('An error occurred while removing staff: ' + error.message);
            }
        }
    }

    async clearDay() {
        if (confirm('Are you sure you want to remove all staff from this day?')) {
            const formData = {
                date: this.currentDay.dataset.date
            };

            try {
                const response = await fetch('/rota/clear-day/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.csrfToken
                    },
                    body: JSON.stringify(formData)
                });

                const data = await response.json();

                if (data.success) {
                    // Clear all staff from the day's DOM
                    this.clearDayDOM(this.currentDay);
                    console.log('Day cleared successfully, removed:', data.deleted_count, 'staff');
                } else {
                    alert('Error: ' + data.error);
                }
            } catch (error) {
                console.error('Error clearing day:', error);
                alert('An error occurred while clearing the day');
            }
        }
        this.contextMenu.style.display = 'none';
    }

    updateDayDOM(data) {
        console.log('updateDayDOM called with data:', data);
        const shift = data.shift;
        const seniorityLevel = shift.seniority_level;
        
        console.log('Updating day for seniority level:', seniorityLevel);
        
        // Update day data attributes
        this.currentDay.dataset.rotaEntryId = data.rota_entry_id;
        this.currentDay.dataset.shiftType = data.shift_type;
        
        // Find the correct seniority row
        const rotaRow = this.currentDay.querySelector(`.rota-row[data-seniority="${seniorityLevel}"]`);
        console.log('Looking for rota row with seniority:', seniorityLevel, 'Found:', rotaRow);
        
        if (rotaRow) {
            console.log('Adding staff span to row');
            // Create new staff span
            const staffSpan = this.createStaffSpan(shift);
            
            // Add to row (gap handles spacing automatically)
            rotaRow.appendChild(staffSpan);
            
            console.log('Staff span added successfully');
        } else {
            console.error('Could not find rota row for seniority level:', seniorityLevel);
        }
        
        // Update NHSP badge if needed
        this.updateNHSPBadge(this.currentDay, data.shift_type);
    }

    createStaffSpan(shift) {
        const staffSpan = document.createElement('span');
        staffSpan.className = 'text-center text-truncate py-1 px-2 d-flex align-items-center justify-content-center staff-entry';
        staffSpan.style.cssText = `
            font-size: 0.8rem; 
            font-weight: 500;
            background-color: ${shift.staff_color}70; 
            color: #333;
            border-radius: 3px;
            flex: 1;
            margin-right: 1px;
            position: relative;
            cursor: default;
            overflow: visible;
        `;
        staffSpan.dataset.shiftId = shift.id;
        staffSpan.dataset.staffId = shift.staff_id;
        
        // Create content container
        const contentContainer = document.createElement('div');
        contentContainer.className = 'd-flex align-items-center justify-content-center w-100';
        contentContainer.textContent = shift.staff_id;
        
        // Add notes icon if there are notes
        if (shift.notes) {
            const notesIcon = document.createElement('i');
            notesIcon.className = 'bi bi-info-circle ms-1';
            notesIcon.title = shift.notes;
            notesIcon.setAttribute('data-bs-toggle', 'tooltip');
            contentContainer.appendChild(notesIcon);
            
            // Reinitialize tooltip
            new bootstrap.Tooltip(notesIcon);
        }
        
        // Create delete button (initially hidden)
        const deleteBtn = document.createElement('i');
        deleteBtn.className = 'bi bi-x-circle-fill staff-delete-btn';
        deleteBtn.style.cssText = `
            position: absolute;
            top: -8px;
            right: -8px;
            font-size: 1rem;
            color: #dc3545;
            cursor: pointer;
            opacity: 0;
            transition: opacity 0.2s ease;
            z-index: 20;
            text-shadow: 1px 1px 2px rgba(255,255,255,0.9), -1px -1px 2px rgba(255,255,255,0.9);
            filter: drop-shadow(0 0 2px rgba(255,255,255,0.8));
        `;
        deleteBtn.title = 'Remove staff from rota';
        
        // Add hover events to show/hide delete button
        staffSpan.addEventListener('mouseenter', () => {
            deleteBtn.style.opacity = '1';
        });
        
        staffSpan.addEventListener('mouseleave', () => {
            deleteBtn.style.opacity = '0';
        });
        
        // Add click event to delete button
        deleteBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.removeStaffFromRota(shift.id, staffSpan);
        });
        
        staffSpan.appendChild(contentContainer);
        staffSpan.appendChild(deleteBtn);
        
        return staffSpan;
    }

    updateNHSPBadge(dayCell, shiftType) {
        // Find the badge container (the header div with date and badges)
        const headerContainer = dayCell.querySelector('.d-flex.justify-content-between.align-items-start.p-1');
        if (!headerContainer) return;
        
        const badgeContainer = headerContainer.querySelector('div:last-child');
        if (!badgeContainer) return;
        
        let nhspBadge = badgeContainer.querySelector('.bg-danger');
        
        if (shiftType === 'nhsp') {
            if (!nhspBadge) {
                nhspBadge = document.createElement('span');
                nhspBadge.className = 'badge bg-danger';
                nhspBadge.style.cssText = 'font-size: 0.6rem;';
                nhspBadge.textContent = 'NHSP';
                badgeContainer.appendChild(nhspBadge);
            }
        } else {
            if (nhspBadge) {
                nhspBadge.remove();
            }
        }
    }

    clearDayDOM(dayCell) {
        // Clear all staff from all seniority rows
        const rotaRows = dayCell.querySelectorAll('.rota-row');
        rotaRows.forEach(row => {
            const staffSpans = row.querySelectorAll('.staff-entry');
            staffSpans.forEach(span => span.remove());
        });
        
        // Find the rota content container (could be .pt-2 or .pt-3)
        let rotaContent = dayCell.querySelector('.pt-2');
        if (!rotaContent) {
            rotaContent = dayCell.querySelector('.pt-3');
        }
        
        if (rotaContent) {
            rotaContent.remove();
        }
        
        // Create the new structured empty day layout
        const emptyStructure = document.createElement('div');
        emptyStructure.className = 'pt-2';
        emptyStructure.style.minHeight = '60px';
        emptyStructure.innerHTML = `
            <!-- Trainee row (empty) -->
            <div class="mb-1 d-flex flex-wrap rota-row"
                 style="min-height: 1.5rem; gap: 1px; overflow: visible;"
                 data-seniority="trainee"
                 data-seniority-name="Trainee">
            </div>
            <!-- On-Call row with "No rota" indicator -->
            <div class="mb-1 d-flex flex-wrap rota-row align-items-center justify-content-center"
                 style="min-height: 1.5rem; gap: 1px; overflow: visible;"
                 data-seniority="oncall"
                 data-seniority-name="On-Call">
                <div class="text-center text-muted" style="font-size: 0.7rem; opacity: 0.6;">
                    <i class="bi bi-dash-circle-dotted"></i>
                    <span class="ms-1">No rota</span>
                </div>
            </div>
            <!-- Senior row (empty) -->
            <div class="mb-1 d-flex flex-wrap rota-row"
                 style="min-height: 1.5rem; gap: 1px; overflow: visible;"
                 data-seniority="senior"
                 data-seniority-name="Senior">
            </div>
        `;
        dayCell.appendChild(emptyStructure);
        
        // Re-attach event handlers to the new rows
        this.attachRotaRowEventHandlers();
        
        // Clear data attributes
        dayCell.dataset.rotaEntryId = '';
        dayCell.dataset.shiftType = 'normal';
        
        // Remove NHSP badge
        this.updateNHSPBadge(dayCell, 'normal');
    }
}

// Initialize the RotaCalendar when the DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // This will be populated by the template
    window.initRotaCalendar = function(availableStaff, csrfToken, staffBySeniority) {
        window.rotaCalendar = new RotaCalendar(availableStaff, csrfToken, staffBySeniority);
    };
});
