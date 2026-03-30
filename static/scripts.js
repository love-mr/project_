/* ═══════════════════════════════════════════════════════
   VaxCare — JavaScript Interactivity
   ═══════════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', () => {
    initSidebar();
    initAlertDismiss();
    initFormEnhancements();
});

/* ─── Sidebar Toggle (Mobile) ───────────────────────── */
function initSidebar() {
    const hamburger = document.getElementById('hamburger');
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebarOverlay');
    const sidebarClose = document.getElementById('sidebarClose');

    function openSidebar() {
        sidebar.classList.add('open');
        overlay.classList.add('show');
        document.body.style.overflow = 'hidden';
    }

    function closeSidebar() {
        sidebar.classList.remove('open');
        overlay.classList.remove('show');
        document.body.style.overflow = '';
    }

    if (hamburger) hamburger.addEventListener('click', openSidebar);
    if (overlay)   overlay.addEventListener('click', closeSidebar);
    if (sidebarClose) sidebarClose.addEventListener('click', closeSidebar);

    // Close on Escape
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') closeSidebar();
    });
}

/* ─── Auto-dismiss Alerts ───────────────────────────── */
function initAlertDismiss() {
    const alerts = document.querySelectorAll('[data-auto-dismiss]');
    alerts.forEach((alert) => {
        setTimeout(() => {
            alert.style.opacity = '0';
            alert.style.transform = 'translateY(-10px)';
            alert.style.transition = 'all 0.4s ease';
            setTimeout(() => alert.remove(), 400);
        }, 5000);
    });
}

/* ─── Form Enhancements ─────────────────────────────── */
function initFormEnhancements() {
    // Add animation to form inputs on focus
    const inputs = document.querySelectorAll('.form-input, input, select, textarea');
    inputs.forEach((input) => {
        input.addEventListener('focus', () => {
            const group = input.closest('.form-group');
            if (group) group.classList.add('focused');
        });
        input.addEventListener('blur', () => {
            const group = input.closest('.form-group');
            if (group) group.classList.remove('focused');
        });
    });

    // Prevent double-submit
    const forms = document.querySelectorAll('form');
    forms.forEach((form) => {
        form.addEventListener('submit', function () {
            const btn = form.querySelector('button[type="submit"]');
            if (btn) {
                btn.disabled = true;
                btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
                // Re-enable after 5s in case of errors
                setTimeout(() => {
                    btn.disabled = false;
                    btn.innerHTML = btn.dataset.originalText || btn.innerHTML;
                }, 5000);
            }
        });
        // Store original text
        const btn = form.querySelector('button[type="submit"]');
        if (btn) btn.dataset.originalText = btn.innerHTML;
    });

    // Date inputs: set min to today for appointment dates
    const dateInputs = document.querySelectorAll('input[type="date"]');
    dateInputs.forEach((input) => {
        if (input.name === 'preferred_date') {
            const today = new Date().toISOString().split('T')[0];
            input.setAttribute('min', today);
        }
    });
}

/* ─── Animate Numbers on Scroll (Stats) ─────────────── */
const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
        if (entry.isIntersecting) {
            const el = entry.target;
            const target = parseInt(el.textContent) || 0;
            if (target > 0 && !el.dataset.animated) {
                el.dataset.animated = 'true';
                animateNumber(el, 0, target, 800);
            }
        }
    });
}, { threshold: 0.5 });

document.querySelectorAll('.stat-number').forEach((el) => observer.observe(el));

function animateNumber(el, start, end, duration) {
    const startTime = performance.now();
    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3); // ease-out cubic
        el.textContent = Math.round(start + (end - start) * eased);
        if (progress < 1) requestAnimationFrame(update);
    }
    requestAnimationFrame(update);
}
