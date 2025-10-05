/**
 * Admin Controls Management JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    initializeAdminControls();
});

/**
 * Initialize admin controls functionality
 */
function initializeAdminControls() {
    // Control toggle switches (exam settings)
    const controlToggles = document.querySelectorAll('.control-toggle');
    controlToggles.forEach(toggle => {
        toggle.addEventListener('change', function() {
            const setting = this.getAttribute('data-setting');
            const isEnabled = this.checked;
            const isSecuritySetting = this.classList.contains('security-control');
            
            // Determine action type based on setting
            let action;
            if (isSecuritySetting) {
                action = 'update_security_setting';
            } else {
                action = 'update_visibility_setting';
            }
            
            updateExamSetting(action, setting, isEnabled, this);
        });
    });

    // Registration Toggle
    const registrationToggle = document.getElementById('toggle-registration');
    if (registrationToggle) {
        registrationToggle.addEventListener('click', function() {
            const isEnabled = this.getAttribute('data-enabled') === 'true';
            toggleRegistration(!isEnabled); // Toggle to opposite state
        });
    }

    // Reset all attempts
    const resetAttemptsBtn = document.getElementById('reset-all-attempts');
    if (resetAttemptsBtn) {
        resetAttemptsBtn.addEventListener('click', function() {
            if (confirm('WARNING: This will delete ALL exam session data. This action cannot be undone. Continue?')) {
                performAdminAction('reset_all_attempts', {});
            }
        });
    }

    // Backup database
    const backupDbBtn = document.getElementById('backup-database');
    if (backupDbBtn) {
        backupDbBtn.addEventListener('click', function() {
            performAdminAction('backup', {});
        });
    }

    // Optimize database
    const optimizeDbBtn = document.getElementById('optimize-database');
    if (optimizeDbBtn) {
        optimizeDbBtn.addEventListener('click', function() {
            performAdminAction('optimize_database', {});
        });
    }

    // Clear cache
    const clearCacheBtn = document.getElementById('clear-cache');
    if (clearCacheBtn) {
        clearCacheBtn.addEventListener('click', function() {
            performAdminAction('clear_cache', {});
        });
    }

    // Refresh system stats
    const refreshStatsBtn = document.getElementById('refresh-stats');
    if (refreshStatsBtn) {
        refreshStatsBtn.addEventListener('click', function() {
            fetchSystemStats();
        });
    }
}

/**
 * Toggle user registration
 * @param {boolean} enable - Whether to enable registration
 */
function toggleRegistration(enable) {
    performAdminAction('toggle_registration', { 
        enabled: enable 
    }, function(response) {
        if (response.success) {
            // Update the button state
            const toggleBtn = document.getElementById('toggle-registration');
            if (toggleBtn) {
                toggleBtn.setAttribute('data-enabled', enable);
                
                if (enable) {
                    toggleBtn.innerHTML = '<i class="fas fa-lock-open"></i> Disable Registration';
                    toggleBtn.classList.remove('btn-success');
                    toggleBtn.classList.add('btn-danger');
                } else {
                    toggleBtn.innerHTML = '<i class="fas fa-lock"></i> Enable Registration';
                    toggleBtn.classList.remove('btn-danger');
                    toggleBtn.classList.add('btn-success');
                }
            }
            
            // Update any status indicators
            const statusIndicator = document.getElementById('registration-status');
            if (statusIndicator) {
                statusIndicator.textContent = enable ? 'Enabled' : 'Disabled';
                statusIndicator.className = enable ? 'text-success' : 'text-danger';
            }
        }
    });
}

/**
 * Fetch system statistics
 */
function fetchSystemStats() {
    performAdminAction('get_system_stats', {}, function(response) {
        if (response.success && response.stats) {
            const stats = response.stats;
            
            // Update all stats on page
            for (const [key, value] of Object.entries(stats)) {
                const element = document.getElementById(`stat-${key}`);
                if (element) {
                    element.textContent = value;
                }
            }
            
            showNotification('Statistics refreshed successfully', 'success');
        }
    });
}

/**
 * Perform an admin action via AJAX
 * @param {string} action - The action to perform
 * @param {object} data - The data to send
 * @param {function} callback - Optional callback function
 */
function performAdminAction(action, data, callback) {
    // Show loading spinner
    const spinner = document.getElementById('loading-spinner');
    if (spinner) spinner.style.display = 'inline-block';
    
    // Get CSRF token
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') ||
                     document.querySelector('input[name="csrf_token"]')?.value;
    
    // Prepare request data
    const requestData = { 
        action: action,
        csrf_token: csrfToken,
        ...data
    };
    
    // Prepare headers
    const headers = {
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest'
    };
    
    if (csrfToken) {
        headers['X-CSRFToken'] = csrfToken;
    }
    
    fetch('/admin/exam_controls', {
        method: 'POST',
        headers: headers,
        body: JSON.stringify(requestData)
    })
    .then(response => {
        if (spinner) spinner.style.display = 'none';
        
        // Check if response is ok
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        // Check content type
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            throw new Error('Server returned non-JSON response. Please check if you are logged in as admin.');
        }
        
        return response.json();
    })
    .then(data => {
        // Only use callback notifications to avoid duplicates
        if (callback && typeof callback === 'function') {
            callback(data);
        } else {
            // Only show notification if no callback is provided
            if (data.success) {
                showNotification(data.message, 'success');
            } else {
                showNotification(data.message || 'An error occurred', 'error');
            }
        }
    })
    .catch(error => {
        if (spinner) spinner.style.display = 'none';
        
        // Better error messages
        let errorMessage = 'An error occurred';
        if (error.message.includes('non-JSON response')) {
            errorMessage = 'Authentication required. Please refresh the page and login again.';
        } else if (error.message.includes('HTTP 401')) {
            errorMessage = 'Authentication failed. Please login as admin.';
        } else if (error.message.includes('HTTP 403')) {
            errorMessage = 'Access denied. Admin privileges required.';
        } else if (error.message.includes('Failed to fetch')) {
            errorMessage = 'Connection error. Please check your internet connection.';
        } else {
            errorMessage = error.message;
        }
        
        showNotification('Error: ' + errorMessage, 'error');
        console.error('Admin Action Error:', error);
    });
}

/**
 * Show notification message
 * @param {string} message - The message to show
 * @param {string} type - The type of notification (success, error, info)
 */
/**
 * Show notification (uses the template's showNotification function)
 * @param {string} message - The message to show
 * @param {string} type - The type of notification (success, error, info)
 */
function showNotification(message, type = 'info') {
    // Use the template's showNotification if available, otherwise create a simple one
    if (window.showNotification && window.showNotification !== this.showNotification) {
        window.showNotification(message, type);
        return;
    }
    
    // Fallback: create simple notification
    const notificationArea = document.querySelector('.notification-container') || createNotificationArea();
    
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show`;
    notification.innerHTML = `
        ${message}
        <button type="button" class="close" data-dismiss="alert" aria-label="Close">
            <span aria-hidden="true">&times;</span>
        </button>
    `;
    
    notificationArea.appendChild(notification);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            notification.remove();
        }, 150);
    }, 5000);
}

/**
 * Create notification area if it doesn't exist
 * @returns {HTMLElement}
 */
function createNotificationArea() {
    const container = document.querySelector('.container');
    const notificationArea = document.createElement('div');
    notificationArea.className = 'notification-container';
    notificationArea.style.position = 'fixed';
    notificationArea.style.top = '20px';
    notificationArea.style.right = '20px';
    notificationArea.style.zIndex = '9999';
    notificationArea.style.width = '300px';
    
    document.body.appendChild(notificationArea);
    return notificationArea;
}

/**
 * Update exam setting via AJAX
 * @param {string} action - The action type (update_security_setting or update_visibility_setting)
 * @param {string} setting - The setting name
 * @param {boolean} isEnabled - Whether the setting is enabled
 * @param {HTMLElement} toggleElement - The toggle element for feedback
 */
function updateExamSetting(action, setting, isEnabled, toggleElement) {
    // Temporarily disable the toggle to prevent rapid clicking
    toggleElement.disabled = true;
    
    performAdminAction(action, { 
        setting: setting,
        enabled: isEnabled 
    }, function(response) {
        // Re-enable the toggle
        toggleElement.disabled = false;
        
        if (!response.success) {
            // If failed, revert the toggle state
            toggleElement.checked = !isEnabled;
            showNotification('Failed to update setting: ' + response.message, 'error');
        } else {
            showNotification(response.message, 'success');
        }
    });
}