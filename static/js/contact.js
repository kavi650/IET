/**
 * Teslead Equipments - Contact Page JavaScript
 * Handles: Form validation and submission
 */

document.addEventListener('DOMContentLoaded', () => {
    initContactForm();
});

function initContactForm() {
    const form = document.getElementById('contactForm');
    if (!form) return;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        // Validate
        if (!validateForm()) return;

        const submitBtn = document.getElementById('submitBtn');
        const originalText = submitBtn.innerHTML;

        // Loading state
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Submitting...';
        submitBtn.disabled = true;

        const data = {
            name: document.getElementById('contactName').value.trim(),
            email: document.getElementById('contactEmail').value.trim(),
            company: document.getElementById('contactCompany').value.trim(),
            message: document.getElementById('contactMessage').value.trim()
        };

        try {
            const response = await fetch('/api/contact', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (result.success) {
                showToast('✅ Enquiry submitted successfully! We\'ll get back to you within 24 hours.', 'success');
                form.reset();
                clearErrors();
            } else {
                showToast('❌ ' + (result.error || 'Failed to submit enquiry.'), 'error');
            }
        } catch (error) {
            showToast('❌ Server connection failed. Make sure the backend is running.', 'error');
        }

        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    });
}

/* ============================================
   FORM VALIDATION
   ============================================ */
function validateForm() {
    let isValid = true;
    clearErrors();

    // Name
    const name = document.getElementById('contactName');
    if (!name.value.trim()) {
        setError(name);
        isValid = false;
    }

    // Email
    const email = document.getElementById('contactEmail');
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!email.value.trim() || !emailRegex.test(email.value.trim())) {
        setError(email);
        isValid = false;
    }

    // Message
    const message = document.getElementById('contactMessage');
    if (!message.value.trim()) {
        setError(message);
        isValid = false;
    }

    return isValid;
}

function setError(input) {
    const group = input.closest('.form-group');
    if (group) group.classList.add('error');
}

function clearErrors() {
    document.querySelectorAll('.form-group.error').forEach(g => g.classList.remove('error'));
}
