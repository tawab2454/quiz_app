// Initialize category counts
if (!window.categoryQuestions) {
    window.categoryQuestions = {
        easy: 0,
        medium: 0,
        hard: 0,
        unseen: 0,
        image: 0,
        video: 0
    };
}
const categoryQuestions = window.categoryQuestions;

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('createExamForm');
    if (!form) return;

    // Add input event listeners to all form inputs
    const inputs = form.querySelectorAll('input, textarea');
    inputs.forEach(input => {
        input.addEventListener('input', updatePreview);
    });

    // Add specific listeners to category inputs
    ['easy', 'medium', 'hard', 'unseen', 'image', 'video'].forEach(category => {
        const input = document.getElementById(`${category}_questions`);
        if (input) {
            input.addEventListener('input', function() {
                categoryQuestions[category] = parseInt(this.value) || 0;
                updateTotalQuestions();
                updatePreview();
            });
        }
    });

    // Initial preview update
    updatePreview();
    
    // Form validation
    form.addEventListener('submit', function(e) {
        if (!validateForm()) {
            e.preventDefault();
        }
    });
});

function updateTotalQuestions() {
    const total = Object.values(categoryQuestions).reduce((sum, count) => sum + count, 0);
    const totalElement = document.getElementById('total_questions');
    if (totalElement) {
        totalElement.textContent = total;
    }
}

function updatePreview() {
    // Get form values with null checks
    const title = document.getElementById('title')?.value || 'Enter exam title';
    const duration = parseInt(document.getElementById('duration')?.value) || 30;
    const passingScore = parseInt(document.getElementById('passing_score')?.value) || 60;
    const maxAttempts = parseInt(document.getElementById('max_attempts')?.value) || 1;

    // Calculate total questions
    const totalQuestions = Object.values(categoryQuestions).reduce((sum, count) => sum + count, 0);

    // Update preview elements with null checks
    updatePreviewElement('previewTitle', title);
    updatePreviewElement('previewDuration', `${duration} minutes`);
    updatePreviewElement('previewQuestions', `${totalQuestions} questions`);
    updatePreviewElement('previewPassingScore', `${passingScore}%`);
    updatePreviewElement('previewMaxAttempts', `${maxAttempts} ${maxAttempts === 1 ? 'attempt' : 'attempts'}`);

    // Calculate and update time per question
    const timePerQuestion = totalQuestions > 0 ? (duration / totalQuestions).toFixed(1) : 0;
    const timeElement = document.getElementById('previewTimePerQuestion');
    if (timeElement) {
        timeElement.textContent = `${timePerQuestion} minutes`;
        
        // Color code based on time per question
        if (parseFloat(timePerQuestion) < 1.5) {
            timeElement.style.color = '#dc3545'; // Red for too little time
        } else if (parseFloat(timePerQuestion) < 2.5) {
            timeElement.style.color = '#ffc107'; // Yellow for borderline
        } else {
            timeElement.style.color = '#28a745'; // Green for good amount of time
        }
    }
}

function updatePreviewElement(id, value) {
    const element = document.getElementById(id);
    if (element) {
        element.textContent = value;
    }
}

function validateForm() {
    const title = document.getElementById('title')?.value.trim();
    const duration = parseInt(document.getElementById('duration')?.value);
    const totalQuestions = Object.values(categoryQuestions).reduce((sum, count) => sum + count, 0);
    const passingScore = parseInt(document.getElementById('passing_score')?.value);
    const maxAttempts = parseInt(document.getElementById('max_attempts')?.value);

    if (!title) {
        showError('Please enter an exam title');
        return false;
    }

    const durationInput = document.getElementById('duration');
    if (!duration || duration < 5 || duration > 300) {
        durationInput.value = Math.max(5, Math.min(300, duration || 5));
        showError('Duration must be between 5 and 300 minutes');
        return false;
    }

    if (totalQuestions < 1) {
        showError('Please select at least one question from any category');
        return false;
    }

    if (!passingScore || passingScore < 0 || passingScore > 100) {
        showError('Passing score must be between 0 and 100');
        return false;
    }

    if (!maxAttempts || maxAttempts < 1 || maxAttempts > 10) {
        showError('Maximum attempts must be between 1 and 10');
        return false;
    }

    const timePerQuestion = duration / totalQuestions;
    if (timePerQuestion < 1) {
        return confirm('Warning: Less than 1 minute per question may be too challenging. Continue anyway?');
    }

    return true;
}

function showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'alert alert-danger';
    errorDiv.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 1000; padding: 1rem; background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; border-radius: 4px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);';
    errorDiv.innerHTML = `
        <strong>Error:</strong> ${message}
        <button type="button" style="float: right; border: none; background: none; color: #721c24; font-weight: bold;" onclick="this.parentElement.remove()">&times;</button>
    `;
    document.body.appendChild(errorDiv);
    setTimeout(() => errorDiv.remove(), 5000);
}