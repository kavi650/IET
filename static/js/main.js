/**
 * Teslead Equipments - Main JavaScript
 * Handles: Navbar, Dark Mode, Scroll Animations, Counter, Mini Chat, Toast
 */

document.addEventListener('DOMContentLoaded', () => {
    initNavbar();
    initDarkMode();
    initScrollAnimations();
    initCounters();
    initMiniChat();
    initParticles();
});

/* ============================================
   NAVBAR
   ============================================ */
function initNavbar() {
    const navbar = document.getElementById('navbar');
    const hamburger = document.getElementById('hamburger');
    const navLinks = document.getElementById('navLinks');

    // Scroll effect
    window.addEventListener('scroll', () => {
        if (window.scrollY > 50) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    });

    // Hamburger toggle
    if (hamburger && navLinks) {
        hamburger.addEventListener('click', () => {
            hamburger.classList.toggle('active');
            navLinks.classList.toggle('open');
        });

        // Close on link click
        navLinks.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => {
                hamburger.classList.remove('active');
                navLinks.classList.remove('open');
            });
        });

        // Close on outside click
        document.addEventListener('click', (e) => {
            if (!navbar.contains(e.target)) {
                hamburger.classList.remove('active');
                navLinks.classList.remove('open');
            }
        });
    }
}

/* ============================================
   DARK MODE
   ============================================ */
function initDarkMode() {
    const toggle = document.getElementById('themeToggle');
    const html = document.documentElement;
    const saved = localStorage.getItem('teslead-theme');

    if (saved) {
        html.setAttribute('data-theme', saved);
        updateToggleIcon(saved);
    }

    if (toggle) {
        toggle.addEventListener('click', () => {
            const current = html.getAttribute('data-theme');
            const next = current === 'dark' ? 'light' : 'dark';
            html.setAttribute('data-theme', next);
            localStorage.setItem('teslead-theme', next);
            updateToggleIcon(next);
        });
    }
}

function updateToggleIcon(theme) {
    const toggle = document.getElementById('themeToggle');
    if (toggle) {
        toggle.innerHTML = theme === 'dark'
            ? '<i class="fas fa-sun"></i>'
            : '<i class="fas fa-moon"></i>';
    }
}

/* ============================================
   SCROLL ANIMATIONS (Intersection Observer)
   ============================================ */
function initScrollAnimations() {
    const reveals = document.querySelectorAll('.reveal, .reveal-left, .reveal-right');

    if (reveals.length === 0) return;

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                observer.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    });

    reveals.forEach(el => observer.observe(el));
}

/* ============================================
   COUNTER ANIMATION
   ============================================ */
function initCounters() {
    const counters = document.querySelectorAll('.counter');

    if (counters.length === 0) return;

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                animateCounter(entry.target);
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.5 });

    counters.forEach(counter => observer.observe(counter));
}

function animateCounter(el) {
    const target = parseInt(el.getAttribute('data-target'));
    const duration = 2000;
    const start = 0;
    const startTime = performance.now();

    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);

        // Ease out cubic
        const eased = 1 - Math.pow(1 - progress, 3);
        const current = Math.floor(eased * target);

        el.textContent = current.toLocaleString();

        if (progress < 1) {
            requestAnimationFrame(update);
        } else {
            el.textContent = target.toLocaleString();
        }
    }

    requestAnimationFrame(update);
}

/* ============================================
   FLOATING PARTICLES (Hero)
   ============================================ */
function initParticles() {
    const container = document.getElementById('heroParticles');
    if (!container) return;

    for (let i = 0; i < 30; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';
        particle.style.left = Math.random() * 100 + '%';
        particle.style.animationDelay = Math.random() * 15 + 's';
        particle.style.animationDuration = (10 + Math.random() * 15) + 's';
        particle.style.width = (2 + Math.random() * 4) + 'px';
        particle.style.height = particle.style.width;
        container.appendChild(particle);
    }
}

/* ============================================
   MINI CHAT WIDGET
   ============================================ */
function initMiniChat() {
    const floatBtn = document.getElementById('chatbotFloatBtn');
    const miniChat = document.getElementById('miniChat');
    const closeBtn = document.getElementById('closeMiniChat');
    const input = document.getElementById('miniChatInput');
    const sendBtn = document.getElementById('miniChatSend');
    const messages = document.getElementById('miniChatMessages');

    if (!floatBtn || !miniChat) return;

    // Toggle mini chat
    floatBtn.addEventListener('click', () => {
        miniChat.classList.toggle('open');
        if (miniChat.classList.contains('open')) {
            input?.focus();
        }
    });

    // Close
    if (closeBtn) {
        closeBtn.addEventListener('click', () => {
            miniChat.classList.remove('open');
        });
    }

    // Suggestion chips
    miniChat.querySelectorAll('.suggestion-chip').forEach(chip => {
        chip.addEventListener('click', () => {
            const query = chip.getAttribute('data-q');
            if (input) input.value = query;
            sendMiniMessage(query, messages, input);
        });
    });

    // Send message
    if (sendBtn && input) {
        sendBtn.addEventListener('click', () => {
            const query = input.value.trim();
            if (query) sendMiniMessage(query, messages, input);
        });

        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                const query = input.value.trim();
                if (query) sendMiniMessage(query, messages, input);
            }
        });
    }
}

async function sendMiniMessage(query, messagesContainer, input) {
    // Add user message
    const userBubble = document.createElement('div');
    userBubble.className = 'chat-bubble user';
    userBubble.textContent = query;
    messagesContainer.appendChild(userBubble);

    input.value = '';

    // Show typing
    const typing = document.createElement('div');
    typing.className = 'typing-indicator';
    typing.innerHTML = '<span></span><span></span><span></span>';
    messagesContainer.appendChild(typing);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query })
        });

        const data = await response.json();
        typing.remove();

        const aiBubble = document.createElement('div');
        aiBubble.className = 'chat-bubble ai';
        aiBubble.innerHTML = formatMessage(data.response);
        messagesContainer.appendChild(aiBubble);
    } catch (error) {
        typing.remove();
        const errBubble = document.createElement('div');
        errBubble.className = 'chat-bubble ai';
        errBubble.textContent = 'Sorry, I\'m having trouble connecting. Please try again.';
        messagesContainer.appendChild(errBubble);
    }

    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

/* ============================================
   FORMAT MESSAGE (Markdown-like)
   ============================================ */
function formatMessage(text) {
    if (!text) return '';

    // Convert markdown-style formatting
    let html = text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')  // Bold
        .replace(/\*(.*?)\*/g, '<em>$1</em>')              // Italic
        .replace(/^• /gm, '‣ ')                            // Bullet
        .replace(/\n/g, '<br>')                             // Newlines
        .replace(/\|(.+)\|/g, (match) => {                  // Simple table detection
            return match;
        });

    return html;
}

/* ============================================
   TOAST NOTIFICATIONS
   ============================================ */
function showToast(message, type = 'success') {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const icons = {
        success: '<i class="fas fa-check-circle" style="color:#22c55e"></i>',
        error: '<i class="fas fa-exclamation-circle" style="color:#ef4444"></i>',
        warning: '<i class="fas fa-exclamation-triangle" style="color:#eab308"></i>',
        info: '<i class="fas fa-info-circle" style="color:var(--primary)"></i>'
    };

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <span class="toast-icon">${icons[type] || icons.info}</span>
        <span>${message}</span>
        <button class="toast-close" onclick="this.parentElement.remove()"><i class="fas fa-times"></i></button>
    `;

    container.appendChild(toast);

    // Auto-remove after 5 seconds
    setTimeout(() => {
        toast.style.animation = 'fadeIn 0.3s ease reverse';
        setTimeout(() => toast.remove(), 300);
    }, 5000);
}
