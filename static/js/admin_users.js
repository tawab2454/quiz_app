/**
 * Admin Users Management JavaScript
 * Handles interactions for the admin user management page
 */

document.addEventListener('DOMContentLoaded', function() {
    // Check if modals exist in DOM
    const userModal = document.getElementById('userDetailsModal');
    const confirmModal = document.getElementById('confirmationModal');
    
    console.log('DOM Content Loaded. Checking modals:');
    console.log('- userDetailsModal exists:', !!userModal);
    console.log('- confirmationModal exists:', !!confirmModal);
    
    // Initialize UI components
    initializeDropdowns();
    initializeCheckboxes();
    initializeBulkActions();
    initializeViewButtons();
    initializeSearch();
});

/**
 * Initialize dropdown menus
 */
function initializeDropdowns() {
    const dropdowns = document.querySelectorAll('.dropdown');
    
    dropdowns.forEach(dropdown => {
        const button = dropdown.querySelector('button');
        if (button) {
            button.addEventListener('click', function(event) {
                event.preventDefault();
                dropdown.classList.toggle('active');
            });
        }
    });

    // Close dropdowns when clicking outside
    document.addEventListener('click', function(event) {
        dropdowns.forEach(dropdown => {
            if (!dropdown.contains(event.target)) {
                dropdown.classList.remove('active');
            }
        });
    });
}

/**
 * Initialize checkbox selection functionality
 */
function initializeCheckboxes() {
    const selectAllCheckbox = document.getElementById('selectAll');
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            const isChecked = this.checked;
            getVisibleUserCheckboxes().forEach(checkbox => {
                checkbox.checked = isChecked;
            });
        });
        
        // Update "select all" checkbox when individual checkboxes change
        document.addEventListener('change', function(e) {
            if (e.target.classList.contains('user-select')) {
                updateSelectAllCheckbox();
            }
        });
    }
}

/**
 * Update the "select all" checkbox state based on individual checkboxes
 */
function updateSelectAllCheckbox() {
    const selectAllCheckbox = document.getElementById('selectAll');
    const visibleCheckboxes = getVisibleUserCheckboxes();
    const checkedCount = visibleCheckboxes.filter(cb => cb.checked).length;
    
    if (checkedCount === 0) {
        selectAllCheckbox.checked = false;
        selectAllCheckbox.indeterminate = false;
    } else if (checkedCount === visibleCheckboxes.length) {
        selectAllCheckbox.checked = true;
        selectAllCheckbox.indeterminate = false;
    } else {
        selectAllCheckbox.checked = false;
        selectAllCheckbox.indeterminate = true;
    }
}

/**
 * Get visible user checkboxes (not hidden by search filter)
 */
function getVisibleUserCheckboxes() {
    return Array.from(document.querySelectorAll('.user-select')).filter(checkbox => {
        return checkbox.closest('tr').style.display !== 'none';
    });
}

/**
 * Initialize view user details buttons
 */
function initializeViewButtons() {
    console.log('Initializing view buttons...');
    const viewButtons = document.querySelectorAll('.view-user');
    console.log(`Found ${viewButtons.length} view buttons`);
    
    viewButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const userId = this.getAttribute('data-userid');
            console.log(`View button clicked for user ID: ${userId}`);
            
            if (userId) {
                viewUserDetails(userId);
            } else {
                console.error('No user ID found in data-userid attribute');
            }
        });
    });
}

/**
 * Initialize search functionality
 */
function initializeSearch() {
    const searchInput = document.getElementById('userSearch');
    const clearButton = document.getElementById('clearSearch');
    const userCount = document.getElementById('userCount');
    
    if (!searchInput) return;
    
    // Search input event
    searchInput.addEventListener('input', function() {
        filterUsers(this.value);
    });
    
    // Clear search button
    if (clearButton) {
        clearButton.addEventListener('click', function() {
            searchInput.value = '';
            filterUsers('');
            searchInput.focus();
        });
    }
    
    // Update initial count
    updateUserCount();
}

/**
 * Filter users based on search term
 */
function filterUsers(searchTerm) {
    const rows = document.querySelectorAll('.users-table tbody tr');
    let visibleCount = 0;
    
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        const isVisible = text.includes(searchTerm.toLowerCase());
        
        row.style.display = isVisible ? '' : 'none';
        if (isVisible) visibleCount++;
    });
    
    updateUserCount(visibleCount);
    updateSelectAllCheckbox(); // Update select all state after filtering
}

/**
 * Update user count display
 */
function updateUserCount(count) {
    const userCount = document.getElementById('userCount');
    if (userCount) {
        if (count !== undefined) {
            userCount.textContent = `${count} users found`;
        } else {
            const visibleRows = document.querySelectorAll('.users-table tbody tr:not([style*="display: none"])');
            userCount.textContent = `${visibleRows.length} users found`;
        }
    }
}

/**
 * Initialize bulk action buttons
 */
function initializeBulkActions() {
    // Bulk delete button
    const bulkDeleteBtn = document.getElementById('bulkDeleteBtn');
    if (bulkDeleteBtn) {
        bulkDeleteBtn.addEventListener('click', function(e) {
            e.preventDefault();
            const selectedCount = document.querySelectorAll('.user-select:checked').length;
            
            if (selectedCount === 0) {
                showAlert('Please select at least one user to delete', 'warning');
                return;
            }
            
            showConfirmation(
                'Confirm Bulk Delete', 
                `Are you sure you want to delete ${selectedCount} selected users? This action cannot be undone.`,
                function() {
                    const selectedUsers = Array.from(document.querySelectorAll('.user-select:checked'))
                        .map(checkbox => checkbox.value);
                    
                    // Use AJAX to delete the users
                    fetch(bulkDeleteEndpoint, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-Requested-With': 'XMLHttpRequest'
                        },
                        body: JSON.stringify({
                            user_ids: selectedUsers
                        })
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            showAlert(data.message, 'success');
                            // Reload the page after a short delay
                            setTimeout(() => {
                                window.location.reload();
                            }, 1000);
                        } else {
                            showAlert(data.message || 'Failed to delete users', 'error');
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        showAlert('Failed to delete users. Please try again.', 'error');
                    });
                }
            );
        });
    }
    
    // Bulk reset exams button
    const bulkResetExamsBtn = document.getElementById('bulkResetExamsBtn');
    if (bulkResetExamsBtn) {
        bulkResetExamsBtn.addEventListener('click', function(e) {
            e.preventDefault();
            const selectedCount = document.querySelectorAll('.user-select:checked').length;
            
            if (selectedCount === 0) {
                showAlert('Please select at least one user to reset exam attempts', 'warning');
                return;
            }
            
            showConfirmation(
                'Reset Exam Attempts', 
                `Are you sure you want to reset exam attempts for ${selectedCount} selected users? This will clear their exam history and allow them to retake exams.`,
                function() {
                    const selectedUsers = Array.from(document.querySelectorAll('.user-select:checked'))
                        .map(checkbox => checkbox.value);
                    
                    // Use AJAX to reset exam attempts
                    fetch(bulkResetEndpoint, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-Requested-With': 'XMLHttpRequest'
                        },
                        body: JSON.stringify({
                            user_ids: selectedUsers
                        })
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            showAlert(data.message, 'success');
                            // No need to reload the page for reset operations
                        } else {
                            showAlert(data.message || 'Failed to reset exam attempts', 'error');
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        showAlert('Failed to reset exam attempts. Please try again.', 'error');
                    });
                }
            );
        });
    }
}

/**
 * Show user details in a modal
 * @param {number} userId - The user ID to view details for
 */
function viewUserDetails(userId) {
    console.log(`Fetching user details for ID: ${userId}`);
    
    // Make sure we're using the correct URL format
    const url = `/admin/users?action=view&user_id=${userId}`;
    console.log(`Request URL: ${url}`);
    
    fetch(url, {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => {
        console.log(`Response status: ${response.status}`);
        if (!response.ok) {
            throw new Error(`Network response was not ok: ${response.status}`);
        }
        return response.json().catch(err => {
            console.error('Error parsing JSON:', err);
            throw new Error('Failed to parse server response as JSON');
        });
    })
    .then(data => {
        console.log('Response data:', data);
        if (data.success) {
            const userDetailsModal = document.getElementById('userDetailsModal');
            const userDetails = document.getElementById('userDetails');
            
            if (!userDetailsModal || !userDetails) {
                console.error('Could not find modal elements:', {
                    userDetailsModal: !!userDetailsModal,
                    userDetails: !!userDetails
                });
                alert('Error: Modal elements not found in the DOM');
                return;
            }
            
            userDetails.innerHTML = data.html;
            console.log('Modal content updated, now opening modal');
            
            // Ensure modal is visible
            userDetailsModal.style.display = 'flex';
            userDetailsModal.style.opacity = '1';
            document.body.style.overflow = 'hidden';
            
            console.log('Modal should now be visible');
        } else {
            showAlert(data.message || 'Failed to load user details', 'error');
        }
    })
    .catch(error => {
        console.error('Error fetching user details:', error);
        showAlert('Failed to load user details. Please try again.', 'error');
    });
}

/**
 * Open a modal by ID
 * @param {string} modalId - The ID of the modal to open
 */
function openModal(modalId) {
    console.log(`Attempting to open modal: ${modalId}`);
    const modal = document.getElementById(modalId);
    
    if (modal) {
        console.log('Modal element found');
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden'; // Prevent scrolling when modal is open
        
        // Force repaint to ensure the modal appears
        setTimeout(() => {
            modal.style.opacity = '1';
        }, 10);
        
        console.log('Modal should now be visible');
    } else {
        console.error(`Modal with ID "${modalId}" not found in the document`);
        alert(`Could not find modal: ${modalId}`);
    }
}

/**
 * Close a modal by ID
 * @param {string} modalId - The ID of the modal to close
 */
function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = ''; // Restore scrolling
    }
}

/**
 * Close the user details modal
 */
function closeUserModal() {
    const modal = document.getElementById('userDetailsModal');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = '';
    }
}

/**
 * Display a confirmation modal
 * @param {string} title - The title of the confirmation dialog
 * @param {string} message - The message to display
 * @param {Function} confirmCallback - Function to call when confirmed
 */
function showConfirmation(title, message, confirmCallback) {
    const titleElement = document.getElementById('confirmationTitle');
    const messageElement = document.getElementById('confirmationMessage');
    const confirmBtn = document.getElementById('confirmBtn');
    
    if (titleElement) titleElement.textContent = title;
    if (messageElement) messageElement.textContent = message;
    
    if (confirmBtn) {
        // Remove any existing event listeners
        const newConfirmBtn = confirmBtn.cloneNode(true);
        confirmBtn.parentNode.replaceChild(newConfirmBtn, confirmBtn);
        
        // Add new event listener
        newConfirmBtn.addEventListener('click', function() {
            confirmCallback();
            closeConfirmationModal();
        });
    }
    
    openModal('confirmationModal');
}

/**
 * Close the confirmation modal
 */
function closeConfirmationModal() {
    closeModal('confirmationModal');
}

/**
 * Display an alert message
 * @param {string} message - The message to display
 * @param {string} type - The type of alert ('success', 'error', 'warning', 'info')
 */
function showAlert(message, type = 'info') {
    // Check if we already have an alert container
    let alertContainer = document.querySelector('.alert-container');
    
    // If not, create one
    if (!alertContainer) {
        alertContainer = document.createElement('div');
        alertContainer.className = 'alert-container';
        document.body.appendChild(alertContainer);
    }
    
    // Create alert element
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.innerHTML = `
        <div class="alert-content">${message}</div>
        <button class="alert-close">&times;</button>
    `;
    
    // Add close button functionality
    const closeButton = alert.querySelector('.alert-close');
    closeButton.addEventListener('click', () => {
        alert.classList.add('alert-fadeout');
        setTimeout(() => {
            alert.remove();
        }, 300);
    });
    
    // Add alert to container
    alertContainer.appendChild(alert);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        if (alert.parentNode) {
            alert.classList.add('alert-fadeout');
            setTimeout(() => {
                if (alert.parentNode) {
                    alert.remove();
                }
            }, 300);
        }
    }, 5000);
}