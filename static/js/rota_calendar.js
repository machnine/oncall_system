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
        this.dateContextMenu = document.getElementById('dateContextMenu');
        this.staffContextMenu = document.getElementById('staffContextMenu');
        
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

    attachDayEventHandlers() {
        // Add right-click context menu to date numbers for day management
        document.querySelectorAll('.date-number').forEach(dateNumber => {
            dateNumber.addEventListener('contextmenu', (e) => {
                e.preventDefault();
                e.stopPropagation();
                const dayDiv = dateNumber.closest('.rota-day');
                if (dayDiv) {
                    this.currentDay = dayDiv;
                    this.showDateManagementMenu(e.pageX, e.pageY);
                }
            });
        });

        // Add right-click context menu to seniority rows for staff selection
        document.querySelectorAll('.rota-row').forEach(row => {
            row.addEventListener('contextmenu', (e) => {
                e.preventDefault();
                e.stopPropagation();
                const dayDiv = row.closest('.rota-day');
                const seniorityLevel = row.dataset.seniority;
                const seniorityName = row.dataset.seniorityName;
                if (dayDiv && seniorityLevel) {
                    this.currentDay = dayDiv;
                    this.currentSeniorityLevel = seniorityLevel;
                    this.currentSeniorityName = seniorityName;
                    this.showStaffSelectionMenu(e.pageX, e.pageY);
                }
            });
        });
    }

    showDateManagementMenu(x, y) {
        // First show the menu temporarily to get its dimensions
        this.dateContextMenu.style.display = 'block';
        this.dateContextMenu.style.visibility = 'hidden';
        
        const rect = this.dateContextMenu.getBoundingClientRect();
        
        // Check if menu would go off-screen horizontally
        if (x + rect.width > window.innerWidth) {
            x = window.innerWidth - rect.width - 10;
        }
        
        // Check if menu would go off-screen vertically
        if (y + rect.height > window.innerHeight) {
            // Position menu above the click point instead of below
            y = y - rect.height - 5;
        }
        
        // Ensure menu doesn't go above the top of the viewport
        if (y < 0) {
            y = 5;
        }
        
        this.dateContextMenu.style.left = x + 'px';
        this.dateContextMenu.style.top = y + 'px';
        this.dateContextMenu.style.visibility = 'visible';
        
        // Update the NHSP toggle text
        this.updateDateMenuText();
    }

    showStaffSelectionMenu(x, y) {
        // First show the menu temporarily to get its dimensions
        this.staffContextMenu.style.display = 'block';
        this.staffContextMenu.style.visibility = 'hidden';
        
        // Update the header and populate staff list first to get accurate dimensions
        this.updateStaffMenu();
        
        const rect = this.staffContextMenu.getBoundingClientRect();
        
        // Check if menu would go off-screen horizontally
        if (x + rect.width > window.innerWidth) {
            x = window.innerWidth - rect.width - 10;
        }
        
        // Check if menu would go off-screen vertically
        if (y + rect.height > window.innerHeight) {
            // Position menu above the click point instead of below
            y = y - rect.height - 5;
        }
        
        // Ensure menu doesn't go above the top of the viewport
        if (y < 0) {
            y = 5;
        }
        
        this.staffContextMenu.style.left = x + 'px';
        this.staffContextMenu.style.top = y + 'px';
        this.staffContextMenu.style.visibility = 'visible';
    }

    attachContextMenuHandlers() {
        // Date context menu handlers
        document.getElementById('date-toggle-shift-type').addEventListener('click', (e) => {
            e.preventDefault();
            this.toggleShiftType();
        });

        document.getElementById('date-clear-day').addEventListener('click', (e) => {
            e.preventDefault();
            this.clearDay();
        });
    }

    attachDocumentHandlers() {
        // Hide context menus when clicking elsewhere
        document.addEventListener('click', (e) => {
            if (!this.dateContextMenu.contains(e.target) && !this.staffContextMenu.contains(e.target)) {
                this.dateContextMenu.style.display = 'none';
                this.staffContextMenu.style.display = 'none';
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
            deleteBtn.title = 'Remove staff from rota';
            staffSpan.appendChild(deleteBtn);
        } else {
            // Existing delete button found, no additional styling needed
        }

        // Remove any existing event listeners to avoid duplicates
        const newStaffSpan = staffSpan.cloneNode(true);
        staffSpan.parentNode.replaceChild(newStaffSpan, staffSpan);
        
        // Get the delete button from the new span
        const newDeleteBtn = newStaffSpan.querySelector('.staff-delete-btn');
        
        // Add hover events to show/hide delete button
        newStaffSpan.addEventListener('mouseenter', () => {
            newDeleteBtn.style.opacity = '1';
        });
        
        newStaffSpan.addEventListener('mouseleave', () => {
            newDeleteBtn.style.opacity = '0';
        });
        
        // Add click event to delete button
        newDeleteBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            const shiftId = newStaffSpan.dataset.shiftId;
            this.removeStaffFromRota(shiftId, newStaffSpan);
        });
    }

    updateDateMenuText() {
        const shiftType = this.currentDay.dataset.shiftType;
        const shiftTypeText = document.getElementById('date-shift-type-text');
        
        // Update shift type toggle text
        if (shiftType === 'nhsp') {
            shiftTypeText.textContent = 'Remove NHSP';
        } else {
            shiftTypeText.textContent = 'Set NHSP';
        }
    }

    updateStaffMenu() {
        const seniorityNameSpan = document.getElementById('seniority-name');
        
        // Update seniority name in header
        seniorityNameSpan.textContent = this.currentSeniorityName;
        
        // Populate staff list for the specific seniority level
        this.populateStaffList();
    }

    populateStaffList() {
        const container = document.getElementById('staff-list');
        container.innerHTML = '';
        
        // Always show staff for the selected seniority level (no general selection anymore)
        this.showStaffForSeniority(container);
    }

    showStaffForSeniority(container) {
        // Filter staff by current seniority level
        let staffToShow = this.currentSeniorityLevel && this.staffBySeniority[this.currentSeniorityLevel] 
            ? [...this.staffBySeniority[this.currentSeniorityLevel]]  // Create a copy
            : [];
        
        // Special rule: Include senior staff in on-call list (for when seniors help out)
        if (this.currentSeniorityLevel === 'oncall' && this.staffBySeniority['senior']) {
            staffToShow = [...staffToShow, ...this.staffBySeniority['senior']];
        }
        
        if (staffToShow.length === 0) {
            const noStaffItem = document.createElement('div');
            noStaffItem.className = 'dropdown-item-text text-muted';            
            noStaffItem.textContent = `No ${this.currentSeniorityName} available`;
            container.appendChild(noStaffItem);
            return;
        }

        // Sort staff to show on-call first, then senior (when both are present)
        if (this.currentSeniorityLevel === 'oncall') {
            staffToShow.sort((a, b) => {
                if (a.seniority_level === 'oncall' && b.seniority_level === 'senior') return -1;
                if (a.seniority_level === 'senior' && b.seniority_level === 'oncall') return 1;
                return 0;
            });
        }
        
        staffToShow.forEach((staff, index) => {
            const staffItem = document.createElement('a');
            staffItem.className = 'dropdown-item d-flex align-items-center';
            staffItem.href = '#';
            
            // Add visual separator between on-call and senior staff
            if (this.currentSeniorityLevel === 'oncall' && index > 0 && 
                staffToShow[index - 1].seniority_level === 'oncall' && 
                staff.seniority_level === 'senior') {
                const separator = document.createElement('div');
                separator.className = 'dropdown-divider';
                container.appendChild(separator);
            }
            
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
        
        this.staffContextMenu.style.display = 'none';
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
                        <div class="mb-1 d-flex flex-wrap rota-row" style="min-height: 1.5rem; gap: 1px; overflow: visible; padding-bottom: 0.25rem;" data-seniority="trainee" data-seniority-name="Trainee"></div>
                        <div class="mb-1 d-flex flex-wrap rota-row align-items-center justify-content-center" style="min-height: 1.5rem; gap: 1px; overflow: visible; background-color: rgba(0, 225, 255, 0.05); border-radius: 2px;" data-seniority="oncall" data-seniority-name="On-Call">
                            <div class="text-center text-muted" style="font-size: 0.7rem; opacity: 0.6;">
                                <i class="bi bi-dash-circle-dotted"></i>
                                <span class="ms-1">No rota</span>
                            </div>
                        </div>
                        <div class="mb-1 d-flex flex-wrap rota-row" style="min-height: 1.5rem; gap: 1px; overflow: visible; padding-bottom: 0.25rem;" data-seniority="senior" data-seniority-name="Senior Cover"></div>
                    </div>
                </div>
            `;
            this.attachDayEventHandlers();
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
        
        this.dateContextMenu.style.display = 'none';
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
                    } else {
                        // There are still staff in other rows, just remove the background from on-call row if it's empty
                        const oncallRow = dayCell.querySelector('.rota-row[data-seniority="oncall"]');
                        if (oncallRow && oncallRow.children.length === 0) {
                            // Remove centering classes and background styling since there are still other staff
                            oncallRow.classList.remove('align-items-center', 'justify-content-center');
                            oncallRow.style.backgroundColor = '';
                            oncallRow.style.borderRadius = '';
                        }
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
        this.dateContextMenu.style.display = 'none';
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
        staffSpan.style.cssText = `background-color: ${shift.staff_color}70;`;
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
        deleteBtn.title = 'Remove staff from rota';
        
        // Add hover events to show/hide delete button (no longer needed with CSS)
        // These can be removed since CSS handles the hover state
        
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
        // Simply clear all staff from existing seniority rows instead of recreating structure
        const rotaRows = dayCell.querySelectorAll('.rota-row');
        rotaRows.forEach(row => {
            const staffSpans = row.querySelectorAll('.staff-entry');
            staffSpans.forEach(span => span.remove());
        });
        
        // Add "No rota" indicator back to the oncall row if it doesn't exist
        const oncallRow = dayCell.querySelector('.rota-row[data-seniority="oncall"]');
        if (oncallRow && !oncallRow.querySelector('.text-muted')) {
            // Add centering classes back
            oncallRow.classList.add('align-items-center', 'justify-content-center');
            
            // Apply the background color styling
            oncallRow.style.backgroundColor = 'rgba(0, 225, 255, 0.05)';
            oncallRow.style.borderRadius = '2px';
            
            // Add the "No rota" indicator
            const noRotaIndicator = document.createElement('div');
            noRotaIndicator.className = 'text-center text-muted';
            noRotaIndicator.style.cssText = 'font-size: 0.7rem; opacity: 0.6;';
            noRotaIndicator.innerHTML = `
                <i class="bi bi-dash-circle-dotted"></i>
                <span class="ms-1">No rota</span>
            `;
            oncallRow.appendChild(noRotaIndicator);
        }
        
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
