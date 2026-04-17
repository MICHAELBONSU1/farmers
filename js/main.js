/* Farmer-Hub Main JavaScript */

// Wait for DOM to be ready
document.addEventListener('DOMContentLoaded', function() {
    
    // Initialize all components
    initNavigation();
    initAnimations();
    initForms();
    initTooltips();
    initScrollEffects();
    
});

// ==================== Navigation ====================

function initNavigation() {
    // Mobile menu toggle
    const hamburger = document.querySelector('.hamburger');
    const navbarMenu = document.querySelector('.navbar-menu');
    
    if (hamburger && navbarMenu) {
        hamburger.addEventListener('click', function() {
            navbarMenu.classList.toggle('active');
            
            // Animate hamburger
            const spans = hamburger.querySelectorAll('span');
            if (navbarMenu.classList.contains('active')) {
                spans[0].style.transform = 'rotate(45deg) translate(5px, 5px)';
                spans[1].style.opacity = '0';
                spans[2].style.transform = 'rotate(-45deg) translate(5px, -5px)';
            } else {
                spans[0].style.transform = 'none';
                spans[1].style.opacity = '1';
                spans[2].style.transform = 'none';
            }
        });
    }
    
    // Close mobile menu when clicking outside
    document.addEventListener('click', function(e) {
        if (navbarMenu && !hamburger.contains(e.target) && !navbarMenu.contains(e.target)) {
            navbarMenu.classList.remove('active');
            const spans = hamburger.querySelectorAll('span');
            spans[0].style.transform = 'none';
            spans[1].style.opacity = '1';
            spans[2].style.transform = 'none';
        }
    });
    
    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            if (href !== '#') {
                e.preventDefault();
                const target = document.querySelector(href);
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            }
        });
    });
}

// ==================== Animations ====================

function initAnimations() {
    // Add entrance animations to cards
    const cards = document.querySelectorAll('.card');
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            card.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 100);
    });
    
    // Parallax effect for background elements
    window.addEventListener('scroll', function() {
        const scrolled = window.pageYOffset;
        const parallaxElements = document.querySelectorAll('.parallax');
        
        parallaxElements.forEach(el => {
            const speed = el.dataset.speed || 0.5;
            el.style.transform = `translateY(${scrolled * speed}px)`;
        });
    });
    
    // Intersection Observer for scroll animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-visible');
            }
        });
    }, observerOptions);
    
    document.querySelectorAll('.animate-on-scroll').forEach(el => {
        observer.observe(el);
    });
    
    // Init chat
    initChat();
    initSearchAutocomplete();
}

// ==================== Forms ====================

function initForms() {
    // Form validation
    const forms = document.querySelectorAll('form[data-validate]');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            let isValid = true;
            const inputs = form.querySelectorAll('[required]');
            
            inputs.forEach(input => {
                if (!input.value.trim()) {
                    isValid = false;
                    input.classList.add('is-invalid');
                } else {
                    input.classList.remove('is-invalid');
                }
            });
            
            if (!isValid) {
                e.preventDefault();
                showAlert('Please fill in all required fields', 'error');
            }
        });
        
        // Real-time validation feedback
        form.querySelectorAll('input, textarea, select').forEach(input => {
            input.addEventListener('blur', function() {
                if (this.hasAttribute('required') && !this.value.trim()) {
                    this.classList.add('is-invalid');
                } else {
                    this.classList.remove('is-invalid');
                }
            });
            
            input.addEventListener('input', function() {
                if (this.classList.contains('is-invalid') && this.value.trim()) {
                    this.classList.remove('is-invalid');
                }
            });
        });
    });
    
    // Password strength indicator
    const passwordInputs = document.querySelectorAll('input[type="password"]');
    passwordInputs.forEach(input => {
        input.addEventListener('input', function() {
            const strength = calculatePasswordStrength(this.value);
            updatePasswordStrength(this, strength);
        });
    });
}

function calculatePasswordStrength(password) {
    let strength = 0;
    
    if (password.length >= 8) strength += 25;
    if (password.match(/[a-z]/) && password.match(/[A-Z]/)) strength += 25;
    if (password.match(/\d/)) strength += 25;
    if (password.match(/[^a-zA-Z\d]/)) strength += 25;
    
    return strength;
}

function updatePasswordStrength(input, strength) {
    let strengthBar = input.parentElement.querySelector('.password-strength');
    
    if (!strengthBar) {
        strengthBar = document.createElement('div');
        strengthBar.className = 'password-strength';
        strengthBar.style.cssText = 'height: 4px; background: #eee; border-radius: 2px; overflow: hidden; margin-top: 5px;';
        strengthBar.innerHTML = '<div class="strength-bar" style="height: 100%; width: 0%; transition: width 0.3s ease;"></div>';
        input.parentElement.appendChild(strengthBar);
    }
    
    const bar = strengthBar.querySelector('.strength-bar');
    bar.style.width = strength + '%';
    
    if (strength <= 25) {
        bar.style.background = '#dc3545';
    } else if (strength <= 50) {
        bar.style.background = '#ffc107';
    } else if (strength <= 75) {
        bar.style.background = '#17a2b8';
    } else {
        bar.style.background = '#28a745';
    }
}

// ==================== Tooltips ====================

function initTooltips() {
    const tooltipElements = document.querySelectorAll('[data-tooltip]');
    
    tooltipElements.forEach(el => {
        const tooltip = document.createElement('div');
        tooltip.className = 'tooltip';
        tooltip.textContent = el.dataset.tooltip;
        tooltip.style.cssText = `
            position: absolute;
            background: #333;
            color: white;
            padding: 5px 10px;
            border-radius: 4px;
            font-size: 12px;
            white-space: nowrap;
            opacity: 0;
            visibility: hidden;
            transition: opacity 0.2s, visibility 0.2s;
            z-index: 1000;
            pointer-events: none;
        `;
        
        el.style.position = 'relative';
        el.appendChild(tooltip);
        
        el.addEventListener('mouseenter', () => {
            const rect = el.getBoundingClientRect();
            tooltip.style.top = (rect.top - tooltip.offsetHeight - 10) + 'px';
            tooltip.style.left = (rect.left + rect.width / 2 - tooltip.offsetWidth / 2) + 'px';
            tooltip.style.opacity = '1';
            tooltip.style.visibility = 'visible';
        });
        
        el.addEventListener('mouseleave', () => {
            tooltip.style.opacity = '0';
            tooltip.style.visibility = 'hidden';
        });
    });
}

// ==================== Scroll Effects ====================

function initScrollEffects() {
    // Navbar background on scroll
    const navbar = document.querySelector('.navbar');
    
    if (navbar) {
        window.addEventListener('scroll', function() {
            if (window.scrollY > 50) {
                navbar.style.boxShadow = '0 4px 20px rgba(0, 0, 0, 0.2)';
            } else {
                navbar.style.boxShadow = '';
            }
        });
    }
    
    // Back to top button
    const backToTop = document.createElement('button');
    backToTop.innerHTML = '↑';
    backToTop.className = 'back-to-top';
    backToTop.style.cssText = `
        position: fixed;
        bottom: 30px;
        right: 30px;
        width: 50px;
        height: 50px;
        border-radius: 50%;
        background: linear-gradient(135deg, #2D5A27, #4A7C43);
        color: white;
        border: none;
        cursor: pointer;
        font-size: 20px;
        box-shadow: 0 4px 15px rgba(45, 90, 39, 0.4);
        opacity: 0;
        visibility: hidden;
        transition: all 0.3s ease;
        z-index: 999;
    `;
    
    document.body.appendChild(backToTop);
    
    window.addEventListener('scroll', () => {
        if (window.scrollY > 300) {
            backToTop.style.opacity = '1';
            backToTop.style.visibility = 'visible';
        } else {
            backToTop.style.opacity = '0';
            backToTop.style.visibility = 'hidden';
        }
    });
    
    backToTop.addEventListener('click', () => {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
}

// ==================== Utilities ====================

function showAlert(message, type = 'info') {
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.textContent = message;
    alert.style.cssText = `
        position: fixed;
        top: 100px;
        right: 20px;
        z-index: 9999;
        max-width: 400px;
        animation: slideInRight 0.3s ease;
    `;
    
    document.body.appendChild(alert);
    
    setTimeout(() => {
        alert.style.animation = 'slideOutRight 0.3s ease forwards';
        setTimeout(() => alert.remove(), 300);
    }, 3000);
}

// Add slideInRight animation
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from {
            opacity: 0;
            transform: translateX(100px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    @keyframes slideOutRight {
        from {
            opacity: 1;
            transform: translateX(0);
        }
        to {
            opacity: 0;
            transform: translateX(100px);
        }
    }
    
    .animate-visible {
        opacity: 1 !important;
        transform: translateY(0) !important;
    }
    
    .animate-on-scroll {
        opacity: 0;
        transform: translateY(30px);
        transition: opacity 0.6s ease, transform 0.6s ease;
    }
    
    .is-invalid {
        border-color: #dc3545 !important;
    }
`;
document.head.appendChild(style);

// ==================== Splash Screen ====================

function initSplash() {
    const splash = document.querySelector('.splash-screen');
    const skipLink = document.querySelector('.splash-skip');
    
    if (splash) {
        // Auto redirect after animation
        setTimeout(() => {
            redirectToLogin();
        }, 4000);
        
        // Skip button
        if (skipLink) {
            skipLink.addEventListener('click', redirectToLogin);
        }
    }
}

function redirectToLogin() {
    const splash = document.querySelector('.splash-screen');
    if (splash) {
        splash.style.animation = 'fadeOut 0.5s ease forwards';
        setTimeout(() => {
            window.location.href = '/login';
        }, 500);
    }
}

// Add fadeOut animation
const fadeStyle = document.createElement('style');
fadeStyle.textContent = `
    @keyframes fadeOut {
        from { opacity: 1; }
        to { opacity: 0; }
    }
`;
document.head.appendChild(fadeStyle);

// Chat functionality
function initChat() {
    // Auto-scroll to bottom on chat load
    const chatMessages = document.getElementById('chatMessages');
    if (chatMessages) {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // Send message AJAX
    const chatForm = document.getElementById('chatForm');
    if (chatForm) {
        chatForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            const sendBtn = this.querySelector('button[type="submit"]');
            sendBtn.textContent = 'Sending...';
            sendBtn.disabled = true;
            
            fetch(this.action, { 
                method: 'POST', 
                body: formData 
            })
            .then(response => {
                if (response.ok) {
                    this.reset();
                    location.reload(); // Reload for simplicity
                } else {
                    throw new Error('Send failed');
                }
            })
            .catch(err => {
                console.error('Send failed', err);
                FarmerHub.showAlert('Failed to send message', 'error');
            })
            .finally(() => {
                sendBtn.textContent = 'Send';
                sendBtn.disabled = false;
            });
        });
    }
    
    // Real-time message polling (simple every 5s)

}

// Search autocomplete
function initSearchAutocomplete() {
    const searchInputs = document.querySelectorAll('.search-box input');
    searchInputs.forEach(input => {
        const searchUrl = input.closest('form')?.action || '/api/search_users';
        input.addEventListener('input', function() {
            if (this.value.length < 2) return;
            
            fetch(`${searchUrl}?q=${encodeURIComponent(this.value)}`)
            .then(res => res.json())
            .then(users => {
                // Show dropdown results (implement dropdown UI)
                console.log('Search results:', users);
            });
        });
    });
}

// Export functions for use in other scripts
window.FarmerHub = {
    showAlert,
    initSplash,
    calculatePasswordStrength,
    initChat,
    initSearchAutocomplete
};

