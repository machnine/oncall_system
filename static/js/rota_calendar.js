/**
 * Rota Calendar JavaScript
 * Handles context menu, staff assignment, and day management functionality
 */

class RotaCalendar {
    constructor(availableStaff, csrfToken) {
        this.availableStaff = availableStaff;
        this.csrfToken = csrfToken;
        this.currentDay = null;
        this.currentSeniorityLevel = null;
        this.currentSeniorityName = null;
        this.contextMenu = document.getElementById('contextMenu');
        
        this.init();
    }

    init() {
        // Initialize Bootstrap tooltips
        this.initTooltips();
        
        // Setup event handlers
        this.attachRotaRowEventHandlers();
        this.attachDayEventHandlers();
        this.attachContextMenuHandlers();
        this.attachDocumentHandlers();
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
            { level: '1', name: 'Trainee' },
            { level: '2', name: 'On Call' },
            { level: '3', name: 'Senior' }
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
        const staffToShow = this.availableStaff;
        
        if (staffToShow.length === 0) {
            const noStaffItem = document.createElement('div');
            noStaffItem.className = 'dropdown-item-text text-muted';
            noStaffItem.textContent = 'No staff available';
            container.appendChild(noStaffItem);
            return;
        }
        
        // Add a back button if we came from seniority selection
        if (this.currentSeniorityName === 'Day') {
            this.addBackButton(container);
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

    addBackButton(container) {
        const backItem = document.createElement('a');
        backItem.className = 'dropdown-item text-secondary';
        backItem.href = '#';
        backItem.innerHTML = '<i class="bi bi-arrow-left"></i> Back to levels';
        backItem.addEventListener('click', (e) => {
            e.preventDefault();
            this.currentSeniorityLevel = null;
            this.currentSeniorityName = 'Day';
            this.populateStaffList();
        });
        container.appendChild(backItem);
        
        const divider = document.createElement('div');
        divider.className = 'dropdown-divider';
        container.appendChild(divider);
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
        const emptyIndicator = this.currentDay.querySelector('.text-center.text-muted');
        if (emptyIndicator) {
            emptyIndicator.remove();
            
            const rotaContent = document.createElement('div');
            rotaContent.className = 'pt-3';
            rotaContent.innerHTML = `
                <div class="mb-1 d-flex rota-row" style="height: 1.75rem;" data-seniority="1" data-seniority-name="Trainee"></div>
                <div class="mb-1 d-flex rota-row" style="height: 1.75rem;" data-seniority="2" data-seniority-name="On-Call"></div>
                <div class="mb-1 d-flex rota-row" style="height: 1.75rem;" data-seniority="3" data-seniority-name="Senior"></div>
            `;
            this.currentDay.appendChild(rotaContent);
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
            const staffSpan = document.createElement('span');
            staffSpan.className = 'text-center text-truncate py-1 px-2 d-flex align-items-center justify-content-center';
            staffSpan.style.cssText = `
                font-size: 0.8rem; 
                font-weight: 500;
                background-color: ${shift.staff_color}70; 
                color: #333;
                border-radius: 3px;
                flex: 1;
                margin-right: 1px;
            `;
            staffSpan.textContent = shift.staff_id;
            
            // Add notes icon if there are notes
            if (shift.notes) {
                const notesIcon = document.createElement('i');
                notesIcon.className = 'bi bi-info-circle ms-1';
                notesIcon.title = shift.notes;
                notesIcon.setAttribute('data-bs-toggle', 'tooltip');
                staffSpan.appendChild(notesIcon);
                
                // Reinitialize tooltip
                new bootstrap.Tooltip(notesIcon);
            }
            
            // Remove margin from last child
            const existingSpans = rotaRow.querySelectorAll('span');
            if (existingSpans.length > 0) {
                existingSpans[existingSpans.length - 1].style.marginRight = '1px';
            }
            staffSpan.style.marginRight = '0px';
            
            // Add to row
            rotaRow.appendChild(staffSpan);
        }
        
        // Update NHSP badge if needed
        this.updateNHSPBadge(this.currentDay, data.shift_type);
    }

    updateNHSPBadge(dayCell, shiftType) {
        // Find the badge container (the second div in the flex container)
        const flexContainer = dayCell.querySelector('.d-flex.justify-content-between.align-items-start.mb-1');
        if (!flexContainer) return;
        
        const badgeContainer = flexContainer.querySelector('div:last-child');
        if (!badgeContainer) return;
        
        let nhspBadge = badgeContainer.querySelector('.bg-danger');
        
        if (shiftType === 'nhsp') {
            if (!nhspBadge) {
                nhspBadge = document.createElement('span');
                nhspBadge.className = 'badge badge-pill bg-danger me-1';
                nhspBadge.style.cssText = 'font-size: 0.6rem; opacity: 0.7;';
                nhspBadge.textContent = 'NHSP';
                badgeContainer.insertBefore(nhspBadge, badgeContainer.firstChild);
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
            const staffSpans = row.querySelectorAll('span');
            staffSpans.forEach(span => span.remove());
        });
        
        // Add empty day indicator
        const rotaContent = dayCell.querySelector('.pt-3');
        if (rotaContent) {
            rotaContent.innerHTML = `
                <div class="text-center text-muted mt-3" style="font-size: 0.8rem;">
                    <i class="bi bi-dash-circle-dotted"></i>
                    <br>
                    <small>No rota</small>
                </div>
            `;
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
    window.initRotaCalendar = function(availableStaff, csrfToken) {
        window.rotaCalendar = new RotaCalendar(availableStaff, csrfToken);
    };
});
