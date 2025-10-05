/* Enhanced Student Dashboard JavaScript */
document.addEventListener('DOMContentLoaded', function() {
    // Active Exam Timer Logic
    const container = document.getElementById('activeExamActions');
    if (container) {
        const startStr = container.getAttribute('data-start');
        const endStr = container.getAttribute('data-end');
        const isActive = container.getAttribute('data-active') === '1';
        const serverNowStr = container.getAttribute('data-server-now');
        const ongoing = container.getAttribute('data-ongoing') === '1';

        const normalize = (s) => (s && s.includes(' ') ? s.replace(' ', 'T') : s);
        const startTime = startStr ? new Date(normalize(startStr)).getTime() : null;
        const endTime = endStr ? new Date(normalize(endStr)).getTime() : null;
        let now = serverNowStr ? new Date(normalize(serverNowStr)).getTime() : Date.now();
        
        const validEndTime = (startTime && endTime && endTime < startTime) ? null : endTime;

        const countdownEl = document.getElementById('preStartCountdown');
        const startBtn = document.getElementById('startExamBtn');
        const resumeBtn = document.getElementById('resumeExamBtn');
        const endedMsg = document.getElementById('examEndedMsg');
        const inactiveMsg = document.getElementById('examInactiveMsg');

        function updateCountdownDisplay(timeLeft) {
            const days = Math.floor(timeLeft / (1000 * 60 * 60 * 24));
            const hours = Math.floor((timeLeft % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
            const minutes = Math.floor((timeLeft % (1000 * 60 * 60)) / (1000 * 60));
            const seconds = Math.floor((timeLeft % (1000 * 60)) / 1000);

            const daysEl = document.getElementById('days');
            const hoursEl = document.getElementById('hours');
            const minutesEl = document.getElementById('minutes');
            const secondsEl = document.getElementById('seconds');

            if (daysEl) daysEl.textContent = String(days).padStart(2, '0');
            if (hoursEl) hoursEl.textContent = String(hours).padStart(2, '0');
            if (minutesEl) minutesEl.textContent = String(minutes).padStart(2, '0');
            if (secondsEl) secondsEl.textContent = String(seconds).padStart(2, '0');
        }

        function showElement(element) {
            if (element) element.style.display = 'block';
        }

        function hideElement(element) {
            if (element) element.style.display = 'none';
        }

        function showStartButton() {
            showElement(startBtn);
            hideElement(countdownEl);
            hideElement(endedMsg);
            hideElement(inactiveMsg);
            hideElement(resumeBtn);
        }

        function showResumeButton() {
            showElement(resumeBtn);
            hideElement(countdownEl);
            hideElement(endedMsg);
            hideElement(inactiveMsg);
            hideElement(startBtn);
        }

        function showCountdown() {
            showElement(countdownEl);
            hideElement(startBtn);
            hideElement(resumeBtn);
            hideElement(endedMsg);
            hideElement(inactiveMsg);
        }

        function showEndedMessage() {
            showElement(endedMsg);
            hideElement(countdownEl);
            hideElement(startBtn);
            hideElement(resumeBtn);
            hideElement(inactiveMsg);
        }

        function showInactiveMessage() {
            showElement(inactiveMsg);
            hideElement(countdownEl);
            hideElement(startBtn);
            hideElement(resumeBtn);
            hideElement(endedMsg);
        }

        // Main logic
        if (!isActive) {
            showInactiveMessage();
            return;
        }

        if (!startTime && !endTime) {
            if (ongoing) {
                showResumeButton();
            } else {
                showStartButton();
            }
            return;
        }

        function updateTimer() {
            now = Date.now();
            
            if (startTime && now < startTime) {
                showCountdown();
                const timeLeft = startTime - now;
                updateCountdownDisplay(timeLeft);
            } else if (validEndTime && now > validEndTime) {
                showEndedMessage();
            } else {
                if (ongoing) {
                    showResumeButton();
                } else {
                    showStartButton();
                }
            }
        }

        updateTimer();
        setInterval(updateTimer, 1000);
    }

    // Add click handlers for exam actions
    const startExamBtn = document.getElementById('startExamBtn');
    const resumeExamBtn = document.getElementById('resumeExamBtn');
    const resultBtns = document.querySelectorAll('.result-btn');

    if (startExamBtn && startExamBtn.hasAttribute('data-url')) {
        startExamBtn.addEventListener('click', function() {
            window.location.href = this.getAttribute('data-url');
        });
    }

    if (resumeExamBtn && resumeExamBtn.hasAttribute('data-url')) {
        resumeExamBtn.addEventListener('click', function() {
            window.location.href = this.getAttribute('data-url');
        });
    }

    // Handle result buttons
    resultBtns.forEach(btn => {
        if (btn.hasAttribute('data-url')) {
            btn.addEventListener('click', function() {
                window.location.href = this.getAttribute('data-url');
            });
        }
    });

    // Add hover effects to cards
    const examCards = document.querySelectorAll('.exam-card, .result-card');
    examCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });

    // Add loading states to buttons
    const actionButtons = document.querySelectorAll('.btn-cyber, .btn-secondary');
    actionButtons.forEach(button => {
        button.addEventListener('click', function() {
            if (!this.disabled) {
                this.classList.add('loading');
                this.disabled = true;
                
                // Re-enable after 3 seconds as failsafe
                setTimeout(() => {
                    this.classList.remove('loading');
                    this.disabled = false;
                }, 3000);
            }
        });
    });
});

// Global function for upcoming exam countdown (called from template)
function initUpcomingCountdown(startTimeStr) {
    const upcomingTimer = document.getElementById('upcomingCountdownTimer');
    if (!upcomingTimer || !startTimeStr) return;
    
    const upcomingStartTime = new Date(startTimeStr.replace(' ', 'T')).getTime();
    
    function updateUpcomingCountdown() {
        const now = Date.now();
        const timeLeft = upcomingStartTime - now;
        
        if (timeLeft > 0) {
            const days = Math.floor(timeLeft / (1000 * 60 * 60 * 24));
            const hours = Math.floor((timeLeft % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
            const minutes = Math.floor((timeLeft % (1000 * 60 * 60)) / (1000 * 60));
            const seconds = Math.floor((timeLeft % (1000 * 60)) / 1000);
            
            upcomingTimer.innerHTML = `
                <div class="countdown-display">
                    <div class="countdown-item">
                        <div class="countdown-number">${String(days).padStart(2, '0')}</div>
                        <div class="countdown-label">Days</div>
                    </div>
                    <div class="countdown-item">
                        <div class="countdown-number">${String(hours).padStart(2, '0')}</div>
                        <div class="countdown-label">Hours</div>
                    </div>
                    <div class="countdown-item">
                        <div class="countdown-number">${String(minutes).padStart(2, '0')}</div>
                        <div class="countdown-label">Minutes</div>
                    </div>
                    <div class="countdown-item">
                        <div class="countdown-number">${String(seconds).padStart(2, '0')}</div>
                        <div class="countdown-label">Seconds</div>
                    </div>
                </div>
                <div class="countdown-caption">⏳ Time until exam opens</div>
            `;
        } else {
            upcomingTimer.innerHTML = '<div class="countdown-caption">🚀 Exam is now available!</div>';
        }
    }
    
    updateUpcomingCountdown();
    setInterval(updateUpcomingCountdown, 1000);
}