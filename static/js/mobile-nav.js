// Enhanced mobile navigation functionality

document.addEventListener('DOMContentLoaded', function() {
    // Mobile navigation toggle
    const navToggle = document.querySelector('.nav-toggle');
    const navMenu = document.querySelector('.nav-menu');
    
    if (navToggle && navMenu) {
        navToggle.addEventListener('click', function() {
            navMenu.classList.toggle('show');
            
            // Update aria-expanded attribute
            const isExpanded = navMenu.classList.contains('show');
            navToggle.setAttribute('aria-expanded', isExpanded);
            
            // Add animation class
            if (isExpanded) {
                setTimeout(() => {
                    navMenu.classList.add('animated');
                }, 10);
            } else {
                navMenu.classList.remove('animated');
            }
        });
        
        // Close menu when clicking outside
        document.addEventListener('click', function(event) {
            const isClickInsideNav = navToggle.contains(event.target) || 
                                    navMenu.contains(event.target);
                                    
            if (!isClickInsideNav && navMenu.classList.contains('show')) {
                navMenu.classList.remove('show');
                navToggle.setAttribute('aria-expanded', 'false');
                navMenu.classList.remove('animated');
            }
        });
        
        // Close menu when pressing escape key
        document.addEventListener('keydown', function(event) {
            if (event.key === 'Escape' && navMenu.classList.contains('show')) {
                navMenu.classList.remove('show');
                navToggle.setAttribute('aria-expanded', 'false');
                navMenu.classList.remove('animated');
            }
        });
        
        // Add swipe support for mobile
        let touchStartX = 0;
        let touchEndX = 0;
        
        document.addEventListener('touchstart', function(event) {
            touchStartX = event.changedTouches[0].screenX;
        }, false);
        
        document.addEventListener('touchend', function(event) {
            touchEndX = event.changedTouches[0].screenX;
            handleSwipe();
        }, false);
        
        function handleSwipe() {
            const swipeThreshold = 100;
            
            if (touchEndX - touchStartX > swipeThreshold && !navMenu.classList.contains('show')) {
                // Swipe right, open menu
                navMenu.classList.add('show');
                navToggle.setAttribute('aria-expanded', 'true');
                setTimeout(() => {
                    navMenu.classList.add('animated');
                }, 10);
            }
            
            if (touchStartX - touchEndX > swipeThreshold && navMenu.classList.contains('show')) {
                // Swipe left, close menu
                navMenu.classList.remove('show');
                navToggle.setAttribute('aria-expanded', 'false');
                navMenu.classList.remove('animated');
            }
        }
    }
    
    // Fix table responsiveness
    const tables = document.querySelectorAll('table:not(.table-responsive)');
    tables.forEach(table => {
        if (!table.parentElement.classList.contains('table-responsive')) {
            const wrapper = document.createElement('div');
            wrapper.className = 'table-responsive';
            table.parentNode.insertBefore(wrapper, table);
            wrapper.appendChild(table);
        }
    });
    
    // Fix image responsiveness
    const images = document.querySelectorAll('img:not(.img-responsive)');
    images.forEach(img => {
        img.classList.add('img-responsive');
        img.style.maxWidth = '100%';
        img.style.height = 'auto';
    });
});