// Form enhancement utilities
document.addEventListener('DOMContentLoaded', function() {
    // Fix password fields visibility and toggle functionality
    const passwordFields = document.querySelectorAll('input[type="password"]');
    
    passwordFields.forEach(field => {
        // Create toggle button if it doesn't exist
        if (!field.nextElementSibling || !field.nextElementSibling.classList.contains('cyber-toggle')) {
            const toggleBtn = document.createElement('button');
            toggleBtn.type = 'button';
            toggleBtn.className = 'cyber-toggle';
            toggleBtn.innerHTML = 'Show';
            toggleBtn.setAttribute('aria-label', 'Toggle password visibility');
            
            toggleBtn.addEventListener('click', function() {
                if (field.type === 'password') {
                    field.type = 'text';
                    this.innerHTML = 'Hide';
                } else {
                    field.type = 'password';
                    this.innerHTML = 'Show';
                }
            });
            
            // Add toggle button after password field in proper container
            const parent = field.parentElement;
            if (parent) {
                if (!parent.classList.contains('form-group')) {
                    parent.classList.add('form-group');
                }
                parent.insertBefore(toggleBtn, field.nextSibling);
            }
        }
    });
    
    // Add consistent styling to all forms
    const allInputs = document.querySelectorAll('input:not([type="checkbox"]):not([type="radio"])');
    allInputs.forEach(input => {
        if (!input.classList.contains('cyber-input') && !input.classList.contains('auth-input')) {
            input.classList.add('cyber-input');
        }
    });
    
    // Fix NSI ID input formatting (uppercase with dash)
    const nsiIdField = document.querySelector('input[name="nsi_id"]');
    if (nsiIdField) {
        nsiIdField.addEventListener('input', function(e) {
            let value = e.target.value.toUpperCase();
            
            // Allow only letters A-D for first character
            if (value.length >= 1) {
                const firstChar = value.charAt(0);
                if (!'ABCD'.includes(firstChar)) {
                    value = value.substring(1);
                }
            }
            
            // Add dash after first character if not present
            if (value.length >= 2) {
                if (value.charAt(1) !== '-') {
                    value = value.charAt(0) + '-' + value.substring(1);
                }
            }
            
            // Limit to format X-YYYY (letter-dash-4digits)
            if (value.length > 6) {
                value = value.substring(0, 6);
            }
            
            // Ensure only digits after dash
            if (value.includes('-')) {
                const parts = value.split('-');
                if (parts.length > 1) {
                    const afterDash = parts[1].replace(/[^0-9]/g, '');
                    value = parts[0] + '-' + afterDash;
                }
            }
            
            e.target.value = value;
        });
        
        nsiIdField.addEventListener('blur', function() {
            // Validate format on blur
            const value = nsiIdField.value;
            const validFormat = /^[A-D]-\d{1,4}$/;
            
            if (value && !validFormat.test(value)) {
                nsiIdField.classList.add('invalid');
                // Show validation message
                let validationMsg = nsiIdField.parentElement.querySelector('.validation-message');
                if (!validationMsg) {
                    validationMsg = document.createElement('div');
                    validationMsg.className = 'validation-message';
                    validationMsg.style.color = 'rgba(255, 100, 100, 0.9)';
                    validationMsg.style.fontSize = '0.85rem';
                    validationMsg.style.marginTop = '5px';
                    nsiIdField.parentElement.appendChild(validationMsg);
                }
                validationMsg.textContent = 'Format should be Letter(A-D)-Numbers(1-4 digits)';
            } else {
                nsiIdField.classList.remove('invalid');
                const validationMsg = nsiIdField.parentElement.querySelector('.validation-message');
                if (validationMsg) {
                    validationMsg.textContent = '';
                }
            }
        });
    }
    
    // Make tables responsive
    const tables = document.querySelectorAll('table');
    tables.forEach(table => {
        const wrapper = document.createElement('div');
        wrapper.className = 'table-responsive';
        wrapper.style.overflowX = 'auto';
        table.parentNode.insertBefore(wrapper, table);
        wrapper.appendChild(table);
    });
    
    // Adjust container width based on screen size
    function adjustContainers() {
        const containers = document.querySelectorAll('.container');
        const maxWidth = window.innerWidth > 1200 ? '1140px' : 
                         window.innerWidth > 992 ? '960px' : 
                         window.innerWidth > 768 ? '720px' : 
                         window.innerWidth > 576 ? '540px' : '95%';
        
        containers.forEach(container => {
            container.style.maxWidth = maxWidth;
        });
    }
    
    // Run on load and resize
    adjustContainers();
    window.addEventListener('resize', adjustContainers);
});