// Admin Results Filter and Export Functions
function getFilterValues() {
    return {
        exam: document.getElementById('examFilter').value,
        wing: document.getElementById('wingFilter').value,
        district: document.getElementById('districtFilter').value,
        section: document.getElementById('sectionFilter').value,
        status: document.getElementById('statusFilter').value,
        search: document.getElementById('searchFilter').value.toLowerCase()
    };
}

// Filter chips functionality
function updateActiveChips() {
    const filters = getFilterValues();
    const chipsContainer = document.querySelector('.active-chips');
    
    if (!chipsContainer) return;
    
    // Clear existing chips (except the container text if any)
    chipsContainer.innerHTML = '';
    
    // Create chips for active filters
    const filterLabels = {
        exam: 'Exam',
        wing: 'Wing',
        district: 'District', 
        section: 'Section',
        status: 'Status',
        search: 'Search'
    };
    
    Object.entries(filters).forEach(([key, value]) => {
        if (value && value.trim() !== '') {
            const chip = createFilterChip(key, value, filterLabels[key]);
            chipsContainer.appendChild(chip);
        }
    });
}

function createFilterChip(filterKey, filterValue, filterLabel) {
    const chip = document.createElement('div');
    chip.className = 'chip';
    
    const chipLabel = document.createElement('span');
    chipLabel.className = 'chip-label';
    chipLabel.textContent = `${filterLabel}: ${filterValue}`;
    
    const clearButton = document.createElement('button');
    clearButton.className = 'chip-clear';
    clearButton.innerHTML = '×';
    clearButton.setAttribute('aria-label', `Remove ${filterLabel} filter`);
    
    clearButton.addEventListener('click', () => {
        clearFilter(filterKey);
    });
    
    chip.appendChild(chipLabel);
    chip.appendChild(clearButton);
    
    return chip;
}

function clearFilter(filterKey) {
    const element = document.getElementById(filterKey + 'Filter');
    if (element) {
        element.value = '';
        applyFilters(true);
        updateActiveChips();
    }
}

function clearAllFilters() {
    const filters = ['exam', 'wing', 'district', 'section', 'status', 'search'];
    filters.forEach(filter => {
        const element = document.getElementById(filter + 'Filter');
        if (element) {
            element.value = '';
        }
    });
    applyFilters(true);
    updateActiveChips();
}

function refreshStats() {
    const filters = getFilterValues();
    const params = new URLSearchParams();
    
    // Add only non-empty filters to URL parameters
    Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null && String(value).trim() !== '') {
            params.append(key, value);
        }
    });
    // Redirect to server with current filters so it recalculates stats and renders page
    const query = params.toString();
    const url = query ? `/admin/results?${query}` : '/admin/results';
    window.location.href = url;
}

function applyFilters(immediate = false) {
    const filters = getFilterValues();
    // Filter the visible rows immediately (client-side)
    filterTable(filters);
    
    // Update active filter chips
    updateActiveChips();

    // If immediate === true, navigate to server with filters so server-side stats update
    if (immediate) {
        const params = new URLSearchParams();
        Object.entries(filters).forEach(([key, value]) => {
            if (value !== undefined && value !== null && String(value).trim() !== '') {
                params.append(key, value);
            }
        });
        window.location.href = `/admin/results?${params.toString()}`;
    }
}

function exportResults() {
    // Redirect to export URL with current filters
    const params = new URLSearchParams(window.location.search);
    window.location.href = `/admin/results/export?${params.toString()}`;
}

function viewDetails(resultId) {
    fetch(`/admin/results/${resultId}/details`)
        .then(response => response.json())
        .then(data => {
            const detailsContent = `
                <div class="result-detail">
                    <h4>Exam Details</h4>
                    <p><strong>Student:</strong> ${data.name} (${data.nsi_id})</p>
                    <p><strong>Exam:</strong> ${data.exam_title}</p>
                    <p><strong>Score:</strong> ${data.score}%</p>
                    <p><strong>Completed:</strong> ${data.end_time}</p>
                    
                    <h4>Questions and Answers</h4>
                    <div class="qa-list">
                        ${data.answers.map((qa, index) => `
                            <div class="qa-item ${qa.is_correct ? 'correct' : 'incorrect'}">
                                <p><strong>Q${index + 1}:</strong> ${qa.question}</p>
                                <p><strong>Selected Answer:</strong> ${qa.selected_answer}</p>
                                <p><strong>Correct Answer:</strong> ${qa.correct_answer}</p>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
            
            document.getElementById('resultDetails').innerHTML = detailsContent;
            document.getElementById('detailsModal').style.display = 'flex';
        });
}

function closeDetailsModal() {
    document.getElementById('detailsModal').style.display = 'none';
}

// Function to filter the table rows
function filterTable(filters) {
    const rows = document.querySelectorAll('.result-row');
    rows.forEach(row => {
        const matches = {
            exam: !filters.exam || row.querySelector('td:nth-child(3)').textContent.trim() === filters.exam,
            wing: !filters.wing || row.querySelector('td:nth-child(6)').textContent.trim() === filters.wing,
            district: !filters.district || row.querySelector('td:nth-child(7)').textContent.trim() === filters.district,
            section: !filters.section || row.querySelector('td:nth-child(8)').textContent.trim() === filters.section,
            status: !filters.status || (
                filters.status === 'passed' ? row.querySelector('.status-badge').textContent.includes('Passed') :
                filters.status === 'failed' ? row.querySelector('.status-badge').textContent.includes('Failed') : true
            ),
            search: !filters.search || row.textContent.toLowerCase().includes(filters.search)
        };

        const showRow = Object.values(matches).every(match => match);
        row.style.display = showRow ? '' : 'none';
    });
}

// Initialize filters when page loads
document.addEventListener('DOMContentLoaded', function() {
    // Set initial filter values from URL parameters
    const params = new URLSearchParams(window.location.search);
    
    if (params.get('exam')) document.getElementById('examFilter').value = params.get('exam');
    if (params.get('wing')) document.getElementById('wingFilter').value = params.get('wing');
    if (params.get('district')) document.getElementById('districtFilter').value = params.get('district');
    if (params.get('section')) document.getElementById('sectionFilter').value = params.get('section');
    if (params.get('status')) document.getElementById('statusFilter').value = params.get('status');
    if (params.get('search')) document.getElementById('searchFilter').value = params.get('search');

    // Initialize active chips display
    updateActiveChips();

    // Add event listeners to all filter elements
    const filters = ['examFilter', 'wingFilter', 'districtFilter', 'sectionFilter', 'statusFilter'];
    filters.forEach(filterId => {
        const element = document.getElementById(filterId);
        if (element) {
            element.addEventListener('change', () => applyFilters(true));
        }
    });

    // Add event listener to search with a small delay
    const searchElement = document.getElementById('searchFilter');
    if (searchElement) {
        let timeout = null;
        searchElement.addEventListener('input', () => {
            clearTimeout(timeout);
            timeout = setTimeout(() => applyFilters(true), 300);
        });
    }
});