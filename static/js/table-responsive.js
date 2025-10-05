// Table responsiveness enhancement

document.addEventListener('DOMContentLoaded', function() {
    // Convert tables to mobile cards on small screens
    function handleTableResponsiveness() {
        const tables = document.querySelectorAll('table:not(.no-responsive)');
        const mobileBreakpoint = 768;
        const isMobile = window.innerWidth <= mobileBreakpoint;
        
        tables.forEach(table => {
            // Skip if already processed
            if (table.getAttribute('data-responsive-processed')) return;
            
            // Mark as processed
            table.setAttribute('data-responsive-processed', 'true');
            
            // Create mobile card container
            const mobileCards = document.createElement('div');
            mobileCards.className = 'mobile-table-card';
            mobileCards.style.display = 'none';
            
            // Get table headers
            const headers = Array.from(table.querySelectorAll('thead th')).map(th => th.textContent.trim());
            
            // Process each row
            const rows = table.querySelectorAll('tbody tr');
            rows.forEach(row => {
                const mobileRow = document.createElement('div');
                mobileRow.className = 'mobile-row';
                
                // Process each cell
                const cells = row.querySelectorAll('td');
                cells.forEach((cell, index) => {
                    // Skip if no header or empty cell
                    if (!headers[index] || !cell.innerHTML.trim()) return;
                    
                    const mobileCell = document.createElement('div');
                    mobileCell.className = 'mobile-cell';
                    
                    const mobileHeader = document.createElement('div');
                    mobileHeader.className = 'mobile-header';
                    mobileHeader.textContent = headers[index];
                    
                    const mobileData = document.createElement('div');
                    mobileData.className = 'mobile-data';
                    mobileData.innerHTML = cell.innerHTML;
                    
                    mobileCell.appendChild(mobileHeader);
                    mobileCell.appendChild(mobileData);
                    mobileRow.appendChild(mobileCell);
                });
                
                mobileCards.appendChild(mobileRow);
            });
            
            // Insert mobile cards before table
            table.parentNode.insertBefore(mobileCards, table);
            
            // Function to toggle visibility based on screen width
            function toggleTableView() {
                const isMobileView = window.innerWidth <= mobileBreakpoint;
                table.style.display = isMobileView ? 'none' : 'table';
                mobileCards.style.display = isMobileView ? 'block' : 'none';
            }
            
            // Initial toggle
            toggleTableView();
            
            // Add resize listener for this table
            window.addEventListener('resize', toggleTableView);
        });
    }
    
    // Run on page load
    handleTableResponsiveness();
    
    // Also run after any AJAX content is loaded
    // This is a generic approach - adjust based on your AJAX implementation
    const originalXHR = window.XMLHttpRequest;
    window.XMLHttpRequest = function() {
        const xhr = new originalXHR();
        xhr.addEventListener('load', function() {
            setTimeout(handleTableResponsiveness, 100);
        });
        return xhr;
    };
});