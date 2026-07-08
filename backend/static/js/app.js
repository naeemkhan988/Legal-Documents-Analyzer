/**
 * app.js — Shared Utilities
 * ==========================
 * Toast notifications, date formatting, fetch helper, sidebar toggle.
 * Loaded on every page via base.html.
 */

// ── Toast Notifications ─────────────────────────────────────────────
function toast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const el = document.createElement('div');
    el.className = `toast toast-${type}`;
    el.innerHTML = `
        <span>${type === 'success' ? '✓' : type === 'error' ? '✕' : 'ℹ'}</span>
        <span>${message}</span>
    `;
    container.appendChild(el);

    // Auto-remove after 4 seconds
    setTimeout(() => {
        el.style.opacity = '0';
        el.style.transform = 'translateX(100%)';
        el.style.transition = 'all 0.3s ease';
        setTimeout(() => el.remove(), 300);
    }, 4000);
}


// ── Fetch JSON Helper ───────────────────────────────────────────────
async function fetchJSON(url, options = {}) {
    const defaults = {
        headers: { 'Content-Type': 'application/json' },
    };
    const merged = { ...defaults, ...options };
    if (options.headers) {
        merged.headers = { ...defaults.headers, ...options.headers };
    }

    const resp = await fetch(url, merged);
    if (!resp.ok) {
        let detail = `HTTP ${resp.status}`;
        try {
            const err = await resp.json();
            detail = err.detail || err.error || detail;
        } catch {}
        throw new Error(detail);
    }
    return resp.json();
}


// ── Date Formatting ─────────────────────────────────────────────────
function formatDate(dateStr) {
    if (!dateStr) return '—';
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-US', {
        month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit'
    });
}


// ── File Size Formatting ────────────────────────────────────────────
function formatFileSize(bytes) {
    if (!bytes) return '0 B';
    const units = ['B', 'KB', 'MB', 'GB'];
    let i = 0;
    let size = bytes;
    while (size >= 1024 && i < units.length - 1) { size /= 1024; i++; }
    return `${size.toFixed(1)} ${units[i]}`;
}


// ── Sidebar Toggle (Mobile) ────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    const toggle = document.getElementById('sidebar-toggle');
    const sidebar = document.getElementById('sidebar');
    if (toggle && sidebar) {
        toggle.addEventListener('click', () => {
            const isOpen = sidebar.classList.contains('w-56');
            sidebar.classList.toggle('w-0', isOpen);
            sidebar.classList.toggle('w-56', !isOpen);
        });
    }
});


// ── Delete Document (used on dashboard) ─────────────────────────────
async function deleteDocument(docId) {
    if (!confirm('Delete this document? This cannot be undone.')) return;
    try {
        await fetchJSON(`/api/documents/${docId}`, { method: 'DELETE' });
        toast('Document deleted', 'success');
        // Remove from DOM or reload
        setTimeout(() => location.reload(), 500);
    } catch (err) {
        toast(err.message || 'Delete failed', 'error');
    }
}
