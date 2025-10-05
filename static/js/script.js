/**
 * Online Examination System - JavaScript Functionality
 * Complete client-side functionality for the examination system
 */

// Global variables
let examTimer = null;
let autoSaveInterval = null;
let currentQuestionIndex = 1;
let totalQuestions = 0;
let timeRemaining = 0;
let examSubmitted = false;
let tabSwitchCount = 0;
let isExamActive = false;

// Security toggle defaults (will be overridden by template values)
let enableCopyProtection = false;
let enableScreenshotBlock = false;
let enableTabSwitchDetect = false;

// Store event listeners for removal
let securityEventListeners = {
    contextmenu: null,
    selectstart: null,
    copy: null,
    cut: null,
    paste: null,
    keydown: [],
    visibilitychange: null
};

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    initMobileHeaderAutoHide();
});

/**
 * Initialize the application based on current page
 */
function initializeApp() {
    const currentPage = getCurrentPage();
    
    switch(currentPage) {
        case 'register':
            initializeRegistration();
            break;
        case 'login':
        case 'admin_login':
            initializeLogin();
            break;
        case 'take_exam':
            initializeExam();
            break;
        case 'admin_dashboard':
            initializeAdminDashboard();
            break;
        case 'admin_questions':
            initializeQuestionManagement();
            break;
        case 'admin_results':
            initializeResultsManagement();
            break;
        default:
            initializeGeneral();
    }
    
    // Initialize common functionality
    initializeFlashMessages();
    initializeFormValidation();
    initializeSecurityFeatures();
}

/**
 * Mobile header auto-hide on scroll
 */
function initMobileHeaderAutoHide() {
    const nav = document.querySelector('.navbar');
    if (!nav) return;
    let lastY = window.scrollY;
    let ticking = false;

    function onScroll() {
        const currentY = window.scrollY;
        const isMobile = window.matchMedia('(max-width: 768px)').matches;
        if (isMobile) {
            if (currentY > lastY && currentY > 20) {
                nav.classList.add('navbar--hidden'); // scrolling down -> hide
            } else {
                nav.classList.remove('navbar--hidden'); // scrolling up -> show
            }
        } else {
            nav.classList.remove('navbar--hidden');
        }
        lastY = currentY;
        ticking = false;
    }

    window.addEventListener('scroll', function() {
        if (!ticking) {
            window.requestAnimationFrame(onScroll);
            ticking = true;
        }
    }, { passive: true });
}

/**
 * Get current page identifier
 */
function getCurrentPage() {
    const path = window.location.pathname;
    const body = document.body;
    
    if (path.includes('/register')) return 'register';
    if (path.includes('/login')) return path.includes('/admin') ? 'admin_login' : 'login';
    if (path.includes('/exam/') && path.includes('/start')) return 'take_exam';
    if (path.includes('/admin/dashboard')) return 'admin_dashboard';
    if (path.includes('/admin/questions')) return 'admin_questions';
    if (path.includes('/admin/results')) return 'admin_results';
    
    return 'general';
}

/**
 * Initialize flash messages functionality
 */
function initializeFlashMessages() {
    const flashMessages = document.querySelectorAll('.flash-message');
    
    flashMessages.forEach(message => {
        // Auto-hide success messages after 5 seconds
        if (message.classList.contains('flash-success')) {
            setTimeout(() => {
                hideFlashMessage(message);
            }, 5000);
        }
        
        // Auto-hide info messages after 4 seconds
        if (message.classList.contains('flash-info')) {
            setTimeout(() => {
                hideFlashMessage(message);
            }, 4000);
        }
    });
}

/**
 * Hide flash message with animation
 */
function hideFlashMessage(message) {
    message.style.opacity = '0';
    message.style.transform = 'translateX(100%)';
    setTimeout(() => {
        message.remove();
    }, 300);
}

/**
 * Initialize registration page functionality
 */
function initializeRegistration() {
    const nsiIdInput = document.getElementById('nsi_id');
    const passwordInput = document.getElementById('password');
    const confirmPasswordInput = document.getElementById('confirm_password');
    const form = document.getElementById('registerForm');
    
    if (!nsiIdInput || !form) return;
    
    // Normalize NSI ID on input to uppercase format A-D-####
    if (nsiIdInput) {
        nsiIdInput.addEventListener('input', function() {
            this.value = normalizeNSIId(this.value);
        });
        nsiIdInput.addEventListener('blur', function() {
            this.value = normalizeNSIId(this.value);
        });
    }
    // Password strength checking
    if (passwordInput) {
        passwordInput.addEventListener('input', function() {
            checkPasswordStrength(this);
            if (confirmPasswordInput && confirmPasswordInput.value) {
                checkPasswordMatch(passwordInput, confirmPasswordInput);
            }
        });
    }
    
    // Password match checking
    if (confirmPasswordInput) {
        confirmPasswordInput.addEventListener('input', function() {
            checkPasswordMatch(passwordInput, this);
        });
    }
    
    // Form submission validation
    form.addEventListener('submit', function(e) {
        if (!validateRegistrationForm()) {
            e.preventDefault();
        } else {
            showLoadingState(form.querySelector('button[type="submit"]'), 'Registering...');
        }
    });
}

/**
 * Format NSI ID input
 */
function formatNSIId(input) {
    input.value = normalizeNSIId(input.value);
}

/**
 * Validate NSI ID format
 */
function validateNSIId(input) {
    const value = normalizeNSIId(input.value);
    input.value = value;
    const isValid = /^[A-D]-[0-9]{4}$/.test(value);
    
    if (value && !isValid) {
        input.setCustomValidity('Please enter a valid NSI ID format (e.g., A-1234)');
        input.classList.add('invalid');
    } else {
        input.setCustomValidity('');
        input.classList.remove('invalid');
    }
}

/**
 * Normalize NSI ID to uppercase A-D and pattern A-0000
 */
function normalizeNSIId(raw) {
    if (!raw) return '';
    let value = String(raw)
        .toUpperCase()
        // unify common dash variants to '-'
        .replace(/[\u2012\u2013\u2014\u2015\u2212]/g, '-')
        // remove whitespace
        .replace(/\s+/g, '')
        // keep only A-D, digits and '-'
        .replace(/[^A-D0-9-]/g, '');

    if (!value) return '';

    const first = value[0] || '';
    if (!/[A-D]/.test(first)) return '';

    let digits = value.slice(1).replace(/-/g, '').replace(/[^0-9]/g, '');
    // Allow up to 4 digits; no padding so backspace works naturally
    digits = digits.slice(0, 4);
    // Insert dash only if there is at least one digit
    return digits.length ? `${first}-${digits}` : first;
}

/**
 * Check password strength
 */
function checkPasswordStrength(passwordInput) {
    const password = passwordInput.value;
    const strengthIndicator = document.getElementById('passwordStrength');
    
    if (!strengthIndicator) return;
    
    let strength = 0;
    let message = '';
    let color = '';
    
    if (password.length >= 6) strength++;
    if (password.match(/[a-z]/)) strength++;
    if (password.match(/[A-Z]/)) strength++;
    if (password.match(/[0-9]/)) strength++;
    if (password.match(/[^a-zA-Z0-9]/)) strength++;
    
    switch(strength) {
        case 0:
        case 1:
            message = 'Very Weak';
            color = '#ff4444';
            break;
        case 2:
            message = 'Weak';
            color = '#ff8800';
            break;
        case 3:
            message = 'Fair';
            color = '#ffaa00';
            break;
        case 4:
            message = 'Good';
            color = '#88cc00';
            break;
        case 5:
            message = 'Strong';
            color = '#00cc44';
            break;
    }
    
    strengthIndicator.textContent = password ? `Strength: ${message}` : '';
    strengthIndicator.style.color = color;
}

/**
 * Check password match
 */
function checkPasswordMatch(passwordInput, confirmPasswordInput) {
    const password = passwordInput.value;
    const confirmPassword = confirmPasswordInput.value;
    const matchIndicator = document.getElementById('passwordMatch');
    
    if (!matchIndicator) return;
    
    if (confirmPassword) {
        if (password === confirmPassword) {
            matchIndicator.textContent = '✓ Passwords match';
            matchIndicator.style.color = '#00cc44';
            confirmPasswordInput.setCustomValidity('');
        } else {
            matchIndicator.textContent = '✗ Passwords do not match';
            matchIndicator.style.color = '#ff4444';
            confirmPasswordInput.setCustomValidity('Passwords do not match');
        }
    } else {
        matchIndicator.textContent = '';
        confirmPasswordInput.setCustomValidity('');
    }
}

/**
 * Validate registration form
 */
function validateRegistrationForm() {
    const nsiIdInput = document.getElementById('nsi_id');
    const nsiId = normalizeNSIId(nsiIdInput.value);
    nsiIdInput.value = nsiId;
    const name = document.getElementById('name').value.trim();
    const password = document.getElementById('password').value;
    const confirmPassword = document.getElementById('confirm_password').value;
    
    // Validate NSI ID format
    if (!/^[A-D]-[0-9]{4}$/.test(nsiId)) {
        showAlert('Please enter a valid NSI ID format (e.g., A-1234)', 'error');
        document.getElementById('nsi_id').focus();
        return false;
    }
    
    // Validate name
    if (!name) {
        showAlert('Please enter your full name', 'error');
        document.getElementById('name').focus();
        return false;
    }
    
    // Validate password
    if (password.length < 6) {
        showAlert('Password must be at least 6 characters long', 'error');
        document.getElementById('password').focus();
        return false;
    }
    
    // Validate password match
    if (password !== confirmPassword) {
        showAlert('Passwords do not match', 'error');
        document.getElementById('confirm_password').focus();
        return false;
    }
    
    return true;
}

/**
 * Initialize login page functionality
 */
function initializeLogin() {
    const form = document.querySelector('form');
    const nsiIdInput = document.getElementById('nsi_id') || document.getElementById('username');
    
    if (!form) return;
    
    // Format NSI ID for student login
    if (nsiIdInput && nsiIdInput.id === 'nsi_id') {
        nsiIdInput.addEventListener('input', function() {
            this.value = this.value.toLowerCase();
        });
    }
    
    // Form submission
    form.addEventListener('submit', function(e) {
        const submitBtn = form.querySelector('button[type="submit"]');
        
        if (validateLoginForm()) {
            showLoadingState(submitBtn, 'Logging in...');
        } else {
            e.preventDefault();
        }
    });
}

/**
 * Validate login form
 */
function validateLoginForm() {
    const nsiIdInput = document.getElementById('nsi_id') || document.getElementById('username');
    const passwordInput = document.getElementById('password');
    
    if (!nsiIdInput.value.trim()) {
        showAlert('Please enter your credentials', 'error');
        nsiIdInput.focus();
        return false;
    }
    
    if (!passwordInput.value) {
        showAlert('Please enter your password', 'error');
        passwordInput.focus();
        return false;
    }
    
    return true;
}

/**
 * Initialize exam functionality
 */
function initializeExam() {
    // Prevent double initialization (which would start multiple timers)
    if (window.__examInitDone) {
        return;
    }
    window.__examInitDone = true;
    const examForm = document.getElementById('examForm');
    const timerElement = document.getElementById('timeRemaining');
    
    if (!examForm || !timerElement) return;
    
    // Get exam parameters from the page
    totalQuestions = document.querySelectorAll('.question-card').length;
    const durationText = timerElement.textContent;
    const [minutes, seconds] = durationText.split(':').map(Number);
    timeRemaining = (minutes * 60) + (seconds || 0);
    
    isExamActive = true;
    console.log('🚀 Exam started - security features activated');
    
    // Initialize exam components
    initializeExamTimer();
    initializeExamNavigation();
    initializeAutoSave();
    initializeExamSecurity();
    initializeExamSubmission();
    
    // Update progress
    updateExamProgress();
    
    // Warn about page refresh
    window.addEventListener('beforeunload', function(e) {
        if (isExamActive && !examSubmitted) {
            e.preventDefault();
            e.returnValue = 'Are you sure you want to leave? Your exam progress may be lost.';
        }
    });
}

/**
 * Initialize exam timer
 */
function initializeExamTimer() {
    const timerElement = document.getElementById('timeRemaining');
    
    examTimer = setInterval(function() {
        timeRemaining--;
        updateTimerDisplay(timerElement);
        
        if (timeRemaining <= 0) {
            clearInterval(examTimer);
            autoSubmitExam();
        } else if (timeRemaining <= 300) { // 5 minutes warning
            document.getElementById('timer').classList.add('timer-warning');
            
            if (timeRemaining === 300) {
                showAlert('⚠️ Warning: Only 5 minutes remaining!', 'warning');
            }
        }
    }, 1000);
}

/**
 * Update timer display
 */
function updateTimerDisplay(timerElement) {
    const minutes = Math.floor(timeRemaining / 60);
    const seconds = timeRemaining % 60;
    const display = `${minutes}:${seconds.toString().padStart(2, '0')}`;
    timerElement.textContent = display;
}

/**
 * Initialize exam navigation
 */
function initializeExamNavigation() {
    // Add keyboard navigation
    document.addEventListener('keydown', function(e) {
        if (!isExamActive) return;
        
        if (e.key === 'ArrowLeft' && currentQuestionIndex > 1) {
            showQuestion(currentQuestionIndex - 1);
        } else if (e.key === 'ArrowRight' && currentQuestionIndex < totalQuestions) {
            showQuestion(currentQuestionIndex + 1);
        }
    });
    
    // Initialize question navigation buttons
    document.querySelectorAll('button[onclick*="showQuestion"]').forEach(button => {
        button.addEventListener('click', function() {
            const match = this.getAttribute('onclick').match(/showQuestion\((\d+)\)/);
            if (match) {
                showQuestion(parseInt(match[1]));
            }
        });
    });
}

/**
 * Show specific question
 */
function showQuestion(questionNumber) {
    // Hide current question and stop any playing videos
    const currentQuestion = document.getElementById(`question${currentQuestionIndex}`);
    if (currentQuestion) {
        currentQuestion.style.display = 'none';
        // Stop videos in current question
        const currentVideos = currentQuestion.querySelectorAll('iframe.youtube-iframe');
        currentVideos.forEach(iframe => {
            try {
                iframe.contentWindow.postMessage(JSON.stringify({
                    'event': 'command',
                    'func': 'stopVideo',
                    'args': ''
                }), '*');
            } catch (e) {
                console.log('Failed to stop video:', e);
            }
        });
    }

    // Show target question
    const targetQuestion = document.getElementById(`question${questionNumber}`);
    if (targetQuestion) {
        targetQuestion.style.display = 'block';
        document.getElementById('reviewScreen').style.display = 'none';

        currentQuestionIndex = questionNumber;
        updateExamProgress();

        // Scroll to top
        window.scrollTo(0, 0);

        // --- NEW CODE FOR IMAGE & YOUTUBE ---
        // Get question data from a global array (assume window.questions)
        const question = window.questions ? window.questions[questionNumber - 1] : null;
        if (question) {
            // Question Image
            const qImgDiv = document.getElementById('question-image');
            if (qImgDiv) {
                if (question.question_image) {
                    qImgDiv.innerHTML = `<img src="${question.question_image}" alt="Question Image">`;
                    qImgDiv.style.display = 'block';
                } else {
                    qImgDiv.style.display = 'none';
                    qImgDiv.innerHTML = '';
                }
            }
            // YouTube Video
            const qYtDiv = document.getElementById('question-youtube');
            if (qYtDiv) {
                if (question.question_youtube) {
                    // If only video ID, convert to full embed URL
                    let ytUrl = question.question_youtube;
                    if (!ytUrl.startsWith('http')) {
                        ytUrl = `https://www.youtube.com/embed/${ytUrl}`;
                    }
                    qYtDiv.innerHTML = `<iframe src="${ytUrl}" allowfullscreen></iframe>`;
                    qYtDiv.style.display = 'block';
                } else {
                    qYtDiv.style.display = 'none';
                    qYtDiv.innerHTML = '';
                }
            }
            // Option Images
            if (question.options && question.option_images) {
                question.options.forEach(function (opt, idx) {
                    let imgHtml = '';
                    if (question.option_images[opt[0]]) {
                        imgHtml = `<img src="${question.option_images[opt[0]]}" alt="Option Image" style="max-width:60px;">`;
                    }
                    const optDiv = document.getElementById('option-' + opt[0]);
                    if (optDiv) {
                        optDiv.innerHTML = `${opt[1]} ${imgHtml}`;
                    }
                });
            }
        }
        // --- END NEW CODE ---
    }
}

/**
 * Update exam progress
 */
function updateExamProgress() {
    const progress = (currentQuestionIndex / totalQuestions) * 100;
    const progressFill = document.getElementById('progressFill');
    const currentQuestionSpan = document.getElementById('currentQuestion');
    
    if (progressFill) {
        progressFill.style.width = progress + '%';
    }
    
    if (currentQuestionSpan) {
        currentQuestionSpan.textContent = currentQuestionIndex;
    }
}

/**
 * Initialize auto-save functionality
 */
function initializeAutoSave() {
    autoSaveInterval = setInterval(function() {
        saveExamProgress();
    }, 10000); // Save every 10 seconds
    
    // Save on answer selection
    document.querySelectorAll('input[type="radio"]').forEach(radio => {
        radio.addEventListener('change', function() {
            saveExamProgress();
        });
    });
}

/**
 * Save exam progress
 */
function saveExamProgress() {
    if (!isExamActive || examSubmitted) return;
    
    const formData = new FormData(document.getElementById('examForm'));
    const answers = {};
    
    for (let [key, value] of formData.entries()) {
        if (key.startsWith('question_')) {
            answers[key] = value;
        }
    }
    
    // Store in localStorage as backup
    localStorage.setItem('examProgress', JSON.stringify({
        answers: answers,
        currentQuestion: currentQuestionIndex,
        timeRemaining: timeRemaining,
        timestamp: Date.now()
    }));
    
    console.log('Exam progress saved');
}

/**
 * Initialize exam security features
 */
function initializeExamSecurity() {
    // Avoid duplicate listeners if we've already attached them successfully
    if (window.__examSecurityInitDone) {
        return;
    }
    let anyAttached = false;

    console.log('🔒 Initializing exam security...');
    console.log('Copy Protection:', enableCopyProtection);
    console.log('Screenshot Block:', enableScreenshotBlock);
    console.log('Tab Switch Detect:', enableTabSwitchDetect);
    console.log('Exam Active:', isExamActive);

    // Copy protection (disable right-click and text selection)
    if (typeof enableCopyProtection !== 'undefined' && enableCopyProtection) {
        console.log('✅ Attaching copy protection listeners');
        document.addEventListener('contextmenu', function(e) {
            e.preventDefault();
            showAlert('Right-click is disabled during the exam', 'warning');
        });

        document.addEventListener('selectstart', function(e) {
            if (e.target.tagName !== 'INPUT' && e.target.tagName !== 'TEXTAREA') {
                e.preventDefault();
            }
        });
        anyAttached = true;
    }    // Tab switch detection
    if (typeof enableTabSwitchDetect !== 'undefined' && enableTabSwitchDetect) {
        console.log('✅ Attaching tab switch detection listeners');
        document.addEventListener('visibilitychange', function() {
            if (document.hidden) {
                tabSwitchCount++;

                if (tabSwitchCount <= 3) {
                    showAlert(`⚠️ Warning: Tab switching detected (${tabSwitchCount}/3). Excessive tab switching may result in automatic submission.`, 'warning');
                } else {
                    showAlert('⚠️ Too many tab switches detected. Your exam will be submitted automatically.', 'error');
                    setTimeout(autoSubmitExam, 3000);
                }
            }
        });
        anyAttached = true;
    }    // Copy protection keyboard shortcuts
    if (typeof enableCopyProtection !== 'undefined' && enableCopyProtection) {
        console.log('✅ Attaching copy protection keyboard listeners');
        document.addEventListener('keydown', function(e) {
            // Disable Ctrl+A, Ctrl+C, Ctrl+V, Ctrl+X, Ctrl+S
            if (e.ctrlKey && ['a', 'c', 'v', 'x', 's'].includes(e.key.toLowerCase())) {
                e.preventDefault();
                showAlert('Copy/cut/paste actions are disabled during the exam', 'warning');
                if (navigator.clipboard && navigator.clipboard.writeText) {
                    navigator.clipboard.writeText('').catch(() => { });
                }
            }
        });
        anyAttached = true;
    }
    
    // Screenshot blocking
    if (typeof enableScreenshotBlock !== 'undefined' && enableScreenshotBlock) {
        console.log('✅ Attaching screenshot blocking listeners');
        document.addEventListener('keydown', function(e) {
            const k = (e.key || '').toLowerCase();
            // PrintScreen key
            if (k === 'printscreen' || k === 'snapshot' || e.keyCode === 44) {
                e.preventDefault();
                showAlert('⚠️ Screenshot attempt detected!', 'error');

                // Clear clipboard
                if (navigator.clipboard && navigator.clipboard.writeText) {
                    navigator.clipboard.writeText('').catch(()=>{});
                }
            }

            // Windows/Mac screen capture shortcuts
            if (e.shiftKey && (e.metaKey || e.ctrlKey)) {
                if (['s','3','4','5'].includes(k)) {
                    e.preventDefault();
                    showAlert('⚠️ Screen capture shortcut detected!', 'error');
                }
            }
        });
        anyAttached = true;
    }    if (anyAttached) {
        window.__examSecurityInitDone = true;
        console.log('🔒 Exam security initialization completed');
    } else {
        console.log('⚠️ No security features were enabled');
    }
    
    // Disable developer tools shortcuts (respect copy protection toggle)
    if (typeof enableCopyProtection !== 'undefined' && enableCopyProtection) {
        console.log('✅ Attaching developer tools blocking listeners');
        document.addEventListener('keydown', function(e) {
            // Disable F12, Ctrl+Shift+I/J (dev tools)
            if (e.key === 'F12' ||
                (e.ctrlKey && e.shiftKey && ['i', 'j'].includes(e.key.toLowerCase()))) {
                e.preventDefault();
                showAlert('Developer tools are disabled during the exam', 'warning');
            }
        });
    }
}

/**
 * Initialize exam submission
 */
function initializeExamSubmission() {
    const examForm = document.getElementById('examForm');
    
    examForm.addEventListener('submit', function(e) {
        // Only prevent default if we want to show confirmation
        if (!examSubmitted) {
            e.preventDefault();
            if (confirmExamSubmission()) {
                submitExam();
            }
        }
    });
}

/**
 * Show review screen
 */
function showReviewScreen() {
    // Hide all questions
    for (let i = 1; i <= totalQuestions; i++) {
        const question = document.getElementById(`question${i}`);
        if (question) {
            question.style.display = 'none';
        }
    }
    
    // Show review screen
    const reviewScreen = document.getElementById('reviewScreen');
    if (reviewScreen) {
        reviewScreen.style.display = 'block';
        populateReviewScreen();
        window.scrollTo(0, 0);
    }
}

/**
 * Populate review screen
 */
function populateReviewScreen() {
    const reviewContainer = document.getElementById('reviewQuestions');
    const form = document.getElementById('examForm');
    
    if (!reviewContainer || !form) return;
    
    let answeredCount = 0;
    let reviewHTML = '';
    
    for (let i = 1; i <= totalQuestions; i++) {
        let isAnswered = false;
        
        // Check if question is answered
        const questionInputs = form.querySelectorAll(`input[name*="question"]:checked`);
        questionInputs.forEach(input => {
            const questionId = input.name.split('_')[1];
            const questionCard = document.getElementById(`question${i}`);
            if (questionCard && questionCard.querySelector(`input[name="question_${questionId}"]`)) {
                isAnswered = true;
            }
        });
        
        if (isAnswered) answeredCount++;
        
        reviewHTML += `
            <div class="review-item ${isAnswered ? 'answered' : 'unanswered'}" 
                 onclick="showQuestion(${i})">
                <div class="review-number">Q${i}</div>
                <div class="review-status">
                    ${isAnswered ? '✅' : '❌'}
                </div>
            </div>
        `;
    }
    
    reviewContainer.innerHTML = reviewHTML;
    
    // Update summary
    const answeredCountElement = document.getElementById('answeredCount');
    const unansweredCountElement = document.getElementById('unansweredCount');
    
    if (answeredCountElement) answeredCountElement.textContent = answeredCount;
    if (unansweredCountElement) unansweredCountElement.textContent = totalQuestions - answeredCount;
}

/**
 * Confirm exam submission
 */
function confirmExamSubmission() {
    const form = document.getElementById('examForm');
    const checkedInputs = form.querySelectorAll('input[type="radio"]:checked');
    const uniqueQuestions = new Set();
    
    checkedInputs.forEach(input => {
        uniqueQuestions.add(input.name);
    });
    
    const answeredCount = uniqueQuestions.size;
    const unansweredCount = totalQuestions - answeredCount;
    
    let message = 'Are you sure you want to submit your exam? This action cannot be undone.';
    if (unansweredCount > 0) {
        message = `You have ${unansweredCount} unanswered question(s). ` + message;
    }
    
    return confirm(message);
}

/**
 * Submit exam
 */
function submitExam() {
    examSubmitted = true;
    isExamActive = false;
    
    // Clear intervals
    if (examTimer) clearInterval(examTimer);
    if (autoSaveInterval) clearInterval(autoSaveInterval);
    
    // Show loading state
    const submitBtn = document.querySelector('button[type="submit"]');
    showLoadingState(submitBtn, 'Submitting...');
    
    // Clear localStorage
    localStorage.removeItem('examProgress');
    
    // Collect form data
    const formData = new FormData(document.getElementById('examForm'));
    
    // Submit via fetch to handle errors properly
    const form = document.getElementById('examForm');
    fetch(form.action, {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (response.ok) {
            // Redirect to the response URL (success page)
            window.location.href = response.url;
        } else {
            throw new Error('Submission failed');
        }
    })
    .catch(error => {
        console.error('Submission error:', error);
        // Fallback to normal form submission
        form.submit();
    });
}

/**
 * Auto-submit exam when time runs out
 */
function autoSubmitExam() {
    showAlert('⏰ Time\'s up! Your exam will be submitted automatically.', 'error');
    
    setTimeout(function() {
        submitExam();
    }, 3000);
}

/**
 * Initialize admin dashboard
 */
function initializeAdminDashboard() {
    // Auto-refresh statistics every 30 seconds
    setInterval(function() {
        location.reload();
    }, 30000);
    
    // Initialize copy to clipboard functionality
    initializeClipboardCopy();
}

/**
 * Initialize clipboard copy functionality
 */
function initializeClipboardCopy() {
    window.copyToClipboard = function(elementId) {
        const element = document.getElementById(elementId);
        if (!element) return;
        
        element.select();
        element.setSelectionRange(0, 99999);
        
        try {
            document.execCommand('copy');
            
            // Show feedback
            const button = element.nextElementSibling;
            if (button) {
                const originalText = button.textContent;
                button.textContent = 'Copied!';
                button.classList.add('btn-success');
                
                setTimeout(() => {
                    button.textContent = originalText;
                    button.classList.remove('btn-success');
                }, 2000);
            }
        } catch (err) {
            showAlert('Failed to copy URL. Please copy manually.', 'error');
        }
    };
}

/**
 * Initialize question management
 */
/**
 * Update question statistics based on visible questions
 */
function updateQuestionStats() {
    const visibleQuestions = document.querySelectorAll('.question-card:not([style*="display: none"])');
    const stats = {
        total: visibleQuestions.length,
        easy: 0,
        medium: 0,
        hard: 0,
        unseen: 0,
        image: 0,
        video: 0
    };

    visibleQuestions.forEach(question => {
        const category = question.getAttribute('data-category');
        if (category in stats) {
            stats[category]++;
        }
    });

    // Update stats display
    document.querySelectorAll('.stat-item').forEach(item => {
        const label = item.querySelector('.stat-label').textContent.toLowerCase();
        const value = item.querySelector('.stat-value');
        if (label in stats) {
            value.textContent = stats[label];
        } else if (label === 'total questions') {
            value.textContent = stats.total;
        }
    });
}

/**
 * Clear all question filters
 */
function clearFilters() {
    const categoryFilter = document.getElementById('categoryFilter');
    if (categoryFilter) {
        categoryFilter.value = '';
        categoryFilter.dispatchEvent(new Event('change'));
    }
}

/**
 * Initialize question management functionality
 */
function initializeQuestionManagement() {
    // Initialize category filter
    const categoryFilter = document.getElementById('categoryFilter');
        if (categoryFilter) {
            categoryFilter.addEventListener('change', function() {
                const selected = this.value;
                const url = new URL(window.location.href);
                if (selected === 'image' || selected === 'video') {
                    url.searchParams.set('category', selected);
                } else if (selected) {
                    url.searchParams.set('category', selected);
                } else {
                    url.searchParams.delete('category');
                }
                window.location.href = url.toString();
            });
        }
    // Initialize modal functionality
    initializeModals();
    
    // Initialize search and filter
    initializeQuestionFilters();
}

/**
 * Initialize modal functionality
 */
/**
 * Initialize modal functionality
 */
/**
 * Initialize modal functionality
 */
function initializeModals() {
    // Edit question modal
    window.editQuestion = function(questionId) {
        const modal = document.getElementById('editModal');
        if (!modal) {
            console.error('Edit modal not found');
            showAlert('Error: Edit modal not found', 'error');
            return;
        }

        console.log('Fetching data for question ID:', questionId); // Debug

        // Fetch question data via AJAX
        fetch(`/admin/questions/${questionId}`, {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/json'
            }
        })
        .then(response => {
            console.log('Fetch response status:', response.status); // Debug
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Fetched question data:', data); // Debug
            if (data.success) {
                // Populate modal fields
                document.getElementById('editQuestionId').value = questionId;
                document.getElementById('editQuestionText').value = data.question.question_text || '';
                document.getElementById('editOption1').value = data.question.option_a || '';
                document.getElementById('editOption2').value = data.question.option_b || '';
                document.getElementById('editOption3').value = data.question.option_c || '';
                document.getElementById('editOption4').value = data.question.option_d || '';
                document.getElementById('editOption5').value = data.question.option_e || '';
                document.getElementById('editOption6').value = data.question.option_f || '';
                
                const optionMap = { 'A': '1', 'B': '2', 'C': '3', 'D': '4', 'E': '5', 'F': '6' };
                document.getElementById('editCorrectOption').value = optionMap[data.question.correct_option] || '';
                
                document.getElementById('editDifficulty').value = data.question.difficulty || 'medium';
                document.getElementById('editSubject').value = data.question.subject || '';
                document.getElementById('editQuestionYouTube').value = data.question.question_youtube || '';

                // Image preview for question
                const imagePreview = document.getElementById('editQuestionImagePreview');
                if (data.question.question_image) {
                    imagePreview.style.display = 'block';
                    imagePreview.innerHTML = `
                        <div class="preview-media">
                            <span class="preview-close" onclick="clearImagePreview('editQuestionImage', 'editQuestionImagePreview')">×</span>
                            <img src="${data.question.question_image}" alt="Question Image">
                        </div>`;
                } else {
                    imagePreview.style.display = 'none';
                    imagePreview.innerHTML = '';
                }

                // YouTube preview
                const youtubePreview = document.getElementById('editQuestionYouTubePreview');
                const videoId = getYouTubeVideoId(data.question.question_youtube);
                if (videoId) {
                    youtubePreview.style.display = 'block';
                    youtubePreview.innerHTML = `
                        <div class="preview-media">
                            <span class="preview-close" onclick="clearYouTubePreview('editQuestionYouTube', 'editQuestionYouTubePreview')">×</span>
                            <iframe src="https://www.youtube.com/embed/${videoId}" 
                                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                                    allowfullscreen></iframe>
                        </div>`;
                } else {
                    youtubePreview.style.display = 'none';
                    youtubePreview.innerHTML = '';
                }

                // Option image previews
                for (let i = 1; i <= 6; i++) {
                    const optImagePreview = document.getElementById(`editOption${i}Preview`);
                    const optImage = data.question[`option_${String.fromCharCode(96 + i)}_image`];
                    if (optImage) {
                        optImagePreview.style.display = 'block';
                        optImagePreview.innerHTML = `
                            <div class="preview-media">
                                <span class="preview-close" onclick="clearImagePreview('editOption${i}Image', 'editOption${i}Preview')">×</span>
                                <img src="${optImage}" alt="Option ${i} Image">
                            </div>`;
                    } else {
                        optImagePreview.style.display = 'none';
                        optImagePreview.innerHTML = '';
                    }
                }

                console.log('Populated editQuestionText:', document.getElementById('editQuestionText').value); // Debug
                console.log('Populated editOption1:', document.getElementById('editOption1').value); // Debug
                console.log('Populated editCorrectOption:', document.getElementById('editCorrectOption').value); // Debug

                modal.style.display = 'flex';
            } else {
                showAlert('Failed to load question data: ' + (data.error || 'Unknown error'), 'error');
            }
        })
        .catch(error => {
            console.error('Fetch error:', error);
            showAlert('Connection error while loading question data. Please check the console.', 'error');
        });
    };
    
    window.closeEditModal = function() {
        const modal = document.getElementById('editModal');
        if (modal) {
            modal.style.display = 'none';
        }
    };
    
    window.saveQuestion = function() {
        const questionId = document.getElementById('editQuestionId').value;
        const form = document.getElementById('editQuestionForm');
        if (!form) {
            console.error('Edit form not found');
            showAlert('Error: Edit form not found', 'error');
            return;
        }

        const formData = new FormData(form);
        console.log('Saving question ID:', questionId); // Debug

        fetch(`/admin/questions/${questionId}/edit`, {
            method: 'POST',
            body: formData
        })
        .then(response => {
            console.log('Save response status:', response.status); // Debug
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Save response data:', data); // Debug
            if (data.success) {
                showAlert('Question updated successfully!', 'success');
                closeEditModal();
                location.reload();
            } else {
                showAlert('Failed to update question: ' + (data.error || 'Unknown error'), 'error');
            }
        })
        .catch(error => {
            console.error('Save error:', error);
            showAlert('Connection error during save. Please check the console.', 'error');
        });
    };
    
    window.deleteQuestion = function(questionId) {
        if (!confirm('Are you sure you want to delete this question? This action cannot be undone.')) {
            return;
        }

        console.log('Attempting to delete question ID:', questionId); // Debug

        fetch(`/admin/questions/${questionId}/delete`, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/json'
            }
        })
        .then(response => {
            console.log('Delete response status:', response.status); // Debug
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Delete response data:', data); // Debug
            if (data.success) {
                const card = document.querySelector(`.question-card[data-question-id="${questionId}"]`);
                if (card) {
                    card.remove();
                    console.log(`Removed card with selector: .question-card[data-question-id="${questionId}"]`); // Debug
                    showAlert('Question deleted successfully!', 'success');
                } else {
                    console.error('UI update failed: No card found for selector: .question-card[data-question-id="' + questionId + '"]'); // Debug
                    showAlert('Question deleted from database, but UI update failed. Please refresh the page.', 'warning');
                }
            } else {
                showAlert('Failed to delete question: ' + (data.error || 'Unknown error'), 'error');
            }
        })
        .catch(error => {
            console.error('Delete error:', error);
            showAlert('Connection error during delete. Please check the console.', 'error');
        });
    };
    
    // Close modal when clicking outside
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('modal')) {
            e.target.style.display = 'none';
        }
    });

    // Image preview function
    window.previewImage = function(input, previewId) {
        const preview = document.getElementById(previewId);
        preview.style.display = 'block';
        preview.innerHTML = '';
        
        if (input.files && input.files[0]) {
            const reader = new FileReader();
            
            reader.onload = function(e) {
                const img = document.createElement('img');
                img.src = e.target.result;
                
                const closeBtn = document.createElement('span');
                closeBtn.className = 'preview-close';
                closeBtn.innerHTML = '×';
                closeBtn.onclick = function(ev) {
                    ev.stopPropagation();
                    preview.style.display = 'none';
                    input.value = '';
                };
                
                const container = document.createElement('div');
                container.className = 'preview-media';
                container.appendChild(closeBtn);
                container.appendChild(img);
    
                preview.appendChild(container);
            }
            
            reader.readAsDataURL(input.files[0]);
        }
    };

    // YouTube link handler
    window.handleYouTubeLink = function(input, previewId) {
        const preview = document.getElementById(previewId);
        const videoId = getYouTubeVideoId(input.value);
        
        if (videoId) {
            preview.style.display = 'block';
            preview.innerHTML = `
                <div class="preview-media">
                    <span class="preview-close" onclick="clearYouTubePreview('${input.id}', '${previewId}')">×</span>
                    <iframe src="https://www.youtube.com/embed/${videoId}" 
                            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                            allowfullscreen></iframe>
                </div>`;
        } else {
            preview.style.display = 'none';
            preview.innerHTML = '';
        }
    };

    // Clear YouTube preview
    window.clearYouTubePreview = function(inputId, previewId) {
        document.getElementById(inputId).value = '';
        document.getElementById(previewId).style.display = 'none';
        document.getElementById(previewId).innerHTML = '';
    };

    // Extract YouTube video ID from URL
    window.getYouTubeVideoId = function(url) {
        if (!url) return null;
        const regExp = /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|&v=)([^#&?]*).*/;
        const match = url.match(regExp);
        return (match && match[2].length === 11) ? match[2] : null;
    };
}



/**
 * Initialize question filters
 */
function initializeQuestionFilters() {
    // Add search functionality if needed
    const searchInput = document.getElementById('questionSearch');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            filterQuestions(this.value);
        });
    }
}

/**
 * Filter questions based on search term
 */
function filterQuestions(searchTerm) {
    const questions = document.querySelectorAll('.question-card');
    const term = searchTerm.toLowerCase();
    
    questions.forEach(question => {
        const text = question.textContent.toLowerCase();
        if (text.includes(term)) {
            question.style.display = 'block';
        } else {
            question.style.display = 'none';
        }
    });
}

/**
 * Initialize results management
 */
function initializeResultsManagement() {
    initializeResultsFilters();
    initializeResultsTable();
    initializeResultsExport();
}

/**
 * Initialize results filters
 */
function initializeResultsFilters() {
    const filters = ['examFilter', 'wingFilter', 'districtFilter', 'sectionFilter', 'statusFilter'];
    
    filters.forEach(filterId => {
        const filter = document.getElementById(filterId);
        if (filter) {
            filter.addEventListener('change', applyFilters);
        }
    });
}

function applyFilters() {
    // Create new URLSearchParams object
    const urlParams = new URLSearchParams();
    
    // Get all filter values
    const filters = {
        exam: document.getElementById('examFilter')?.value,
        wing: document.getElementById('wingFilter')?.value,
        district: document.getElementById('districtFilter')?.value,
        section: document.getElementById('sectionFilter')?.value,
        status: document.getElementById('statusFilter')?.value
    };

    // Only add non-empty filters to URL
    Object.entries(filters).forEach(([key, value]) => {
        if (value && value !== 'All' && value !== '') {
            urlParams.set(key, value);
        }
    });

    // Create new URL with filters or just the pathname if no filters
    const newUrl = urlParams.toString() 
        ? `${window.location.pathname}?${urlParams.toString()}`
        : window.location.pathname;
    window.location.href = newUrl;
}

/**
 * Filter results based on selected criteria
 */
function filterResults() {
    const examFilter = document.getElementById('examFilter')?.value.toLowerCase() || '';
    const wingFilter = document.getElementById('wingFilter')?.value.toLowerCase() || '';
    const statusFilter = document.getElementById('statusFilter')?.value || '';
    const searchFilter = document.getElementById('searchFilter')?.value.toLowerCase() || '';
    
    const rows = document.querySelectorAll('.result-row');
    
    rows.forEach(row => {
        const exam = (row.dataset.exam || '').toLowerCase();
        const wing = (row.dataset.wing || '').toLowerCase();
        const status = row.dataset.status || '';
        const searchText = (row.dataset.search || '').toLowerCase();
        
        let show = true;
        
        if (examFilter && !exam.includes(examFilter)) show = false;
        if (wingFilter && !wing.includes(wingFilter)) show = false;
        if (statusFilter && status !== statusFilter) show = false;
        if (searchFilter && !searchText.includes(searchFilter)) show = false;
        
        row.style.display = show ? '' : 'none';
    });
}

/**
 * Initialize results table sorting
 */
function initializeResultsTable() {
    let sortDirection = {};
    
    window.sortTable = function(columnIndex) {
        const table = document.getElementById('resultsTable');
        if (!table) return;
        
        const tbody = table.querySelector('tbody');
        const rows = Array.from(tbody.querySelectorAll('tr'));
        
        const currentDirection = sortDirection[columnIndex] || 'asc';
        const newDirection = currentDirection === 'asc' ? 'desc' : 'asc';
        sortDirection[columnIndex] = newDirection;
        
        rows.sort((a, b) => {
            const aValue = a.cells[columnIndex].textContent.trim();
            const bValue = b.cells[columnIndex].textContent.trim();
            
            // Handle numeric values (scores)
            if (columnIndex === 3) {
                const aNum = parseFloat(aValue);
                const bNum = parseFloat(bValue);
                return newDirection === 'asc' ? aNum - bNum : bNum - aNum;
            }
            
            // Handle text values
            const comparison = aValue.localeCompare(bValue);
            return newDirection === 'asc' ? comparison : -comparison;
        });
        
        // Clear and re-append sorted rows
        tbody.innerHTML = '';
        rows.forEach(row => tbody.appendChild(row));
        
        // Update sort indicators
        document.querySelectorAll('.sort-indicator').forEach(indicator => {
            indicator.textContent = '↕️';
        });
        
        const currentIndicator = table.querySelector(`th:nth-child(${columnIndex + 1}) .sort-indicator`);
        if (currentIndicator) {
            currentIndicator.textContent = newDirection === 'asc' ? '↑' : '↓';
        }
    };
}

/**
 * Initialize results export
 */
function initializeResultsExport() {
    window.exportResults = function() {
        const rows = document.querySelectorAll('.result-row');
        const visibleRows = Array.from(rows).filter(row => row.style.display !== 'none');
        
        if (visibleRows.length === 0) {
            showAlert('No results to export', 'warning');
            return;
        }
        
        let csv = 'NSI ID,Name,Exam,Score,Status,Wing,District,Completed\n';
        
        visibleRows.forEach(row => {
            const cells = row.querySelectorAll('td');
            const rowData = [
                cells[0].textContent.trim(),
                cells[1].textContent.trim(),
                cells[2].textContent.trim(),
                cells[3].textContent.trim().replace('%', ''),
                cells[4].textContent.trim(),
                cells[5].textContent.trim(),
                cells[6].textContent.trim(),
                cells[7].textContent.trim()
            ];
            
            csv += rowData.map(field => `"${field}"`).join(',') + '\n';
        });
        
        // Create and download file
        const blob = new Blob([csv], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `exam_results_${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        showAlert('Results exported successfully!', 'success');
    };
    
    window.viewDetails = function(resultId) {
        const modal = document.getElementById('detailsModal');
        if (modal) {
            const detailsContent = `
                <div class="result-detail">
                    <h4>Exam Result Details</h4>
                    <p><strong>Result ID:</strong> ${resultId}</p>
                    <p><em>Detailed result information would be displayed here, including:</em></p>
                    <ul>
                        <li>Individual question responses</li>
                        <li>Time taken per question</li>
                        <li>Exam start and end times</li>
                        <li>Answer analysis</li>
                    </ul>
                </div>
            `;
            
            document.getElementById('resultDetails').innerHTML = detailsContent;
            modal.style.display = 'flex';
        }
    };
    
    window.closeDetailsModal = function() {
        const modal = document.getElementById('detailsModal');
        if (modal) {
            modal.style.display = 'none';
        }
    };
}

/**
 * Initialize general functionality
 */
function initializeGeneral() {
    // Initialize smooth scrolling
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const href = this.getAttribute('href');
            // Skip if href is just '#'
            if (href === '#') return;
            
            const target = document.querySelector(href);
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });
}

/**
 * Initialize form validation
 */
function initializeFormValidation() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        const inputs = form.querySelectorAll('input, textarea, select');
        
        inputs.forEach(input => {
            input.addEventListener('blur', function() {
                validateField(this);
            });
            
            input.addEventListener('input', function() {
                if (this.classList.contains('invalid')) {
                    validateField(this);
                }
            });
        });
    });
}

/**
 * Validate individual form field
 */
function validateField(field) {
    const value = field.value.trim();
    let isValid = true;
    let message = '';
    
    // Required field validation
    if (field.hasAttribute('required') && !value) {
        isValid = false;
        message = 'This field is required';
    }
    
    // Email validation
    if (field.type === 'email' && value && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
        isValid = false;
        message = 'Please enter a valid email address';
    }
    
    // Password validation
    if (field.type === 'password' && value && value.length < 6) {
        isValid = false;
        message = 'Password must be at least 6 characters long';
    }
    
    // Update field appearance
    if (isValid) {
        field.classList.remove('invalid');
        field.setCustomValidity('');
    } else {
        field.classList.add('invalid');
        field.setCustomValidity(message);
    }
    
    return isValid;
}

/**
 * Initialize security features
 */
function initializeSecurityFeatures() {
    // Add CSRF token to all forms if available
    const csrfToken = document.querySelector('meta[name="csrf-token"]');
    if (csrfToken) {
        document.querySelectorAll('form').forEach(form => {
            if (!form.querySelector('input[name="csrf_token"]')) {
                const input = document.createElement('input');
                input.type = 'hidden';
                input.name = 'csrf_token';
                input.value = csrfToken.getAttribute('content');
                form.appendChild(input);
            }
        });
    }
}

/**
 * Show loading state on button
 */
function showLoadingState(button, text) {
    if (!button) return;
    
    button.disabled = true;
    button.dataset.originalText = button.textContent;
    button.textContent = text;
    button.classList.add('loading');
}

/**
 * Hide loading state on button
 */
function hideLoadingState(button) {
    if (!button) return;
    
    button.disabled = false;
    button.textContent = button.dataset.originalText || button.textContent;
    button.classList.remove('loading');
}

/**
 * Show alert message
 */
function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `flash-message flash-${type}`;
    alertDiv.innerHTML = `
        ${message}
        <button onclick="this.parentElement.remove()" class="flash-close">&times;</button>
    `;
    
    const container = document.querySelector('.flash-messages') || document.body;
    container.insertBefore(alertDiv, container.firstChild);
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            hideFlashMessage(alertDiv);
        }
    }, 5000);
}

/**
 * Toggle password visibility
 */
function togglePassword(fieldId) {
    const field = document.getElementById(fieldId);
    const toggleText = document.getElementById(fieldId + 'ToggleText');
    
    if (!field || !toggleText) return;
    
    if (field.type === 'password') {
        field.type = 'text';
        toggleText.textContent = 'Hide';
    } else {
        field.type = 'password';
        toggleText.textContent = 'Show';
    }
}

/**
 * Utility function to format time
 */
function formatTime(seconds) {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
}

/**
 * Utility function to debounce function calls
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Utility function to throttle function calls
 */
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Make functions available globally
window.showQuestion = showQuestion;
window.showReviewScreen = showReviewScreen;
window.confirmSubmission = function() {
    return confirmExamSubmission();
};

/**
 * Initialize exam security features based on admin settings
 */
function initializeExamSecurity() {
    console.log('🔒 Initializing exam security features...');

    // Read security settings from data attributes on the exam container
    const examContainer = document.querySelector('.exam-container');
    if (examContainer) {
        // Debug: show raw data attribute values
        console.log('Raw data attributes:', {
            copyProtection: examContainer.dataset.enableCopyProtection,
            screenshotBlock: examContainer.dataset.enableScreenshotBlock,
            tabSwitchDetect: examContainer.dataset.enableTabSwitchDetect
        });

        // Convert to boolean - check for '1', 'true', or truthy values
        enableCopyProtection = examContainer.dataset.enableCopyProtection === '1' || 
                              examContainer.dataset.enableCopyProtection === 'True' ||
                              examContainer.dataset.enableCopyProtection === 'true';
        enableScreenshotBlock = examContainer.dataset.enableScreenshotBlock === '1' || 
                               examContainer.dataset.enableScreenshotBlock === 'True' ||
                               examContainer.dataset.enableScreenshotBlock === 'true';
        enableTabSwitchDetect = examContainer.dataset.enableTabSwitchDetect === '1' || 
                               examContainer.dataset.enableTabSwitchDetect === 'True' ||
                               examContainer.dataset.enableTabSwitchDetect === 'true';

        console.log('Security settings from DOM:', {
            enableCopyProtection,
            enableScreenshotBlock,
            enableTabSwitchDetect
        });
    } else {
        console.warn('Exam container not found, using default security settings');
    }

    console.log('Final security toggles:', enableCopyProtection, enableScreenshotBlock, enableTabSwitchDetect);

    // Remove existing security if any
    removeAllSecurityListeners();

    // Apply security based on settings
    if (enableCopyProtection) {
        initializeCopyProtection();
    }

    if (enableScreenshotBlock) {
        initializeScreenshotBlock();
    }

    if (enableTabSwitchDetect) {
        initializeTabSwitchDetection();
    }
}

/**
 * Remove all security event listeners
 */
function removeAllSecurityListeners() {
    console.log('🧹 Removing existing security listeners...');
    
    // Remove contextmenu listener
    if (securityEventListeners.contextmenu) {
        document.removeEventListener('contextmenu', securityEventListeners.contextmenu);
        securityEventListeners.contextmenu = null;
    }
    
    // Remove selectstart listener
    if (securityEventListeners.selectstart) {
        document.removeEventListener('selectstart', securityEventListeners.selectstart);
        securityEventListeners.selectstart = null;
    }
    
    // Remove copy/cut/paste listeners
    if (securityEventListeners.copy) {
        document.removeEventListener('copy', securityEventListeners.copy);
        securityEventListeners.copy = null;
    }
    if (securityEventListeners.cut) {
        document.removeEventListener('cut', securityEventListeners.cut);
        securityEventListeners.cut = null;
    }
    if (securityEventListeners.paste) {
        document.removeEventListener('paste', securityEventListeners.paste);
        securityEventListeners.paste = null;
    }
    
    // Remove keydown listeners
    securityEventListeners.keydown.forEach(listener => {
        document.removeEventListener('keydown', listener);
    });
    securityEventListeners.keydown = [];
    
    // Remove visibility change listener
    if (securityEventListeners.visibilitychange) {
        document.removeEventListener('visibilitychange', securityEventListeners.visibilitychange);
        securityEventListeners.visibilitychange = null;
    }
    
    // Remove security styles
    const securityStyle = document.getElementById('security-styles');
    if (securityStyle) {
        securityStyle.remove();
    }
}

/**
 * Initialize copy protection
 */
function initializeCopyProtection() {
    console.log('🛡️ Enabling copy protection');

    // Disable right-click context menu
    securityEventListeners.contextmenu = function(e) {
        if (isExamActive) {
            e.preventDefault();
            showAlert('❌ Right-click is disabled during the exam', 'error');
            return false;
        }
    };
    document.addEventListener('contextmenu', securityEventListeners.contextmenu);

    // Disable text selection
    securityEventListeners.selectstart = function(e) {
        if (isExamActive) {
            e.preventDefault();
            return false;
        }
    };
    document.addEventListener('selectstart', securityEventListeners.selectstart);

    // Disable copy events
    securityEventListeners.copy = function(e) {
        if (isExamActive) {
            e.preventDefault();
            showAlert('❌ Copying is not allowed during the exam', 'error');
            return false;
        }
    };
    document.addEventListener('copy', securityEventListeners.copy);

    // Disable cut events
    securityEventListeners.cut = function(e) {
        if (isExamActive) {
            e.preventDefault();
            showAlert('❌ Cutting is not allowed during the exam', 'error');
            return false;
        }
    };
    document.addEventListener('cut', securityEventListeners.cut);

    // Disable paste events
    securityEventListeners.paste = function(e) {
        if (isExamActive) {
            e.preventDefault();
            showAlert('❌ Pasting is not allowed during the exam', 'error');
            return false;
        }
    };
    document.addEventListener('paste', securityEventListeners.paste);

    // Disable keyboard shortcuts for copy/cut/paste
    const keydownListener = function(e) {
        if (!isExamActive) return;

        // Ctrl+C, Ctrl+X, Ctrl+V
        if (e.ctrlKey && (e.key === 'c' || e.key === 'x' || e.key === 'v')) {
            e.preventDefault();
            showAlert('❌ Copy/Cut/Paste shortcuts are disabled during the exam', 'error');
            return false;
        }

        // Ctrl+A (select all)
        if (e.ctrlKey && e.key === 'a') {
            e.preventDefault();
            showAlert('❌ Select all is disabled during the exam', 'error');
            return false;
        }
    };
    document.addEventListener('keydown', keydownListener);
    securityEventListeners.keydown.push(keydownListener);
}

/**
 * Initialize screenshot blocking
 */
function initializeScreenshotBlock() {
    console.log('📸 Enabling screenshot blocking');

    // Prevent Print Screen key
    const printScreenListener = function(e) {
        if (isExamActive && e.key === 'PrintScreen') {
            e.preventDefault();
            showAlert('❌ Screenshots are not allowed during the exam', 'error');

            // Clear clipboard (attempt to remove screenshot)
            if (navigator.clipboard) {
                navigator.clipboard.writeText('').catch(() => {});
            }
            return false;
        }
    };
    document.addEventListener('keydown', printScreenListener);
    securityEventListeners.keydown.push(printScreenListener);

    // Prevent screenshot via keyboard shortcuts
    const screenshotShortcutListener = function(e) {
        if (!isExamActive) return;

        // Windows: Windows+Shift+S, Windows+PrintScreen
        if (e.shiftKey && e.key === 's' && (e.metaKey || e.ctrlKey)) {
            e.preventDefault();
            showAlert('❌ Screenshots are not allowed during the exam', 'error');
            return false;
        }
    };
    document.addEventListener('keydown', screenshotShortcutListener);
    securityEventListeners.keydown.push(screenshotShortcutListener);

    // Add CSS to prevent screenshots (limited effectiveness)
    const style = document.createElement('style');
    style.id = 'security-styles';
    style.textContent = `
        body {
            -webkit-user-select: none;
            -moz-user-select: none;
            -ms-user-select: none;
            user-select: none;
            -webkit-touch-callout: none;
        }
    `;
    document.head.appendChild(style);
}

/**
 * Initialize tab switch detection
 */
function initializeTabSwitchDetection() {
    console.log('👁️ Enabling tab switch detection');

    // Detect when user switches tabs/windows
    securityEventListeners.visibilitychange = function() {
        if (!isExamActive) return;

        if (document.hidden) {
            tabSwitchCount++;
            console.log(`🚨 Tab switch detected! Count: ${tabSwitchCount}`);
            
            showAlert(`⚠️ Warning: Tab switch detected (${tabSwitchCount}/5). Please stay on the exam page.`, 'warning');
            
            // Log tab switch for admin
            logTabSwitch(tabSwitchCount);
            
            // Auto-submit after too many switches
            if (tabSwitchCount >= 5) {
                showAlert('⚠️ Too many tab switches detected. Your exam will be submitted automatically.', 'error');
                setTimeout(autoSubmitExam, 3000);
            }
        }
    };
    document.addEventListener('visibilitychange', securityEventListeners.visibilitychange);
}

/**
 * Update security settings dynamically (called from admin panel)
 */
function updateSecuritySettings(copyProtection, screenshotBlock, tabSwitchDetect) {
    console.log('🔄 Updating security settings:', {copyProtection, screenshotBlock, tabSwitchDetect});
    
    // Update global variables
    enableCopyProtection = copyProtection;
    enableScreenshotBlock = screenshotBlock;
    enableTabSwitchDetect = tabSwitchDetect;
    
    // Re-initialize security with new settings
    initializeExamSecurity();
}

/**
 * Get current security status
 */
function getSecurityStatus() {
    return {
        enableCopyProtection,
        enableScreenshotBlock,
        enableTabSwitchDetect,
        isExamActive,
        tabSwitchCount
    };
}
function initializeTabSwitchDetection() {
    console.log('👁️ Enabling tab switch detection');

    // Detect when user switches tabs/windows
    securityEventListeners.visibilitychange = function() {
        if (!isExamActive) return;

        if (document.hidden) {
            tabSwitchCount++;
            console.log(`🚨 Tab switch detected! Count: ${tabSwitchCount}`);
            
            showAlert(`⚠️ Warning: Tab switch detected (${tabSwitchCount}/5). Please stay on the exam page.`, 'warning');
            
            // Log tab switch for admin
            logTabSwitch(tabSwitchCount);
            
            // Auto-submit after too many switches
            if (tabSwitchCount >= 5) {
                showAlert('⚠️ Too many tab switches detected. Your exam will be submitted automatically.', 'error');
                setTimeout(autoSubmitExam, 3000);
            }
        }
    };
    document.addEventListener('visibilitychange', securityEventListeners.visibilitychange);
}

/**
 * Log tab switch to server
 */
function logTabSwitch(count) {
    // Optional: Send tab switch data to server for monitoring
    const examForm = document.getElementById('examForm');
    if (examForm) {
        const sessionId = examForm.dataset.sessionId;
        if (sessionId) {
            // Could make an AJAX call here to log the tab switch
            console.log(`Logging tab switch #${count} for session ${sessionId}`);
        }
    }
}

window.togglePassword = togglePassword;

// Export for module systems if needed
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        initializeApp,
        showAlert,
        formatTime,
        debounce,
        throttle
    };
}