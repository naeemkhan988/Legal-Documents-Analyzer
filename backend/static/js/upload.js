/**
 * upload.js — Drag-Drop File Upload
 * ====================================
 * Handles drag-drop and click-to-browse upload with progress tracking.
 * Uses XMLHttpRequest for upload progress events.
 */

document.addEventListener('DOMContentLoaded', () => {
    const zone = document.getElementById('upload-zone');
    const input = document.getElementById('file-input');
    const progressBar = document.getElementById('upload-progress');
    const fillBar = document.getElementById('upload-fill');
    const percentEl = document.getElementById('upload-percent');
    const filenameEl = document.getElementById('upload-filename');

    if (!zone || !input) return;

    // ── Click to browse ─────────────────────────────────────────────
    zone.addEventListener('click', () => input.click());

    // ── File input change ───────────────────────────────────────────
    input.addEventListener('change', () => {
        if (input.files.length > 0) uploadFile(input.files[0]);
    });

    // ── Drag events ─────────────────────────────────────────────────
    zone.addEventListener('dragover', (e) => {
        e.preventDefault();
        zone.classList.add('border-brand-500', 'bg-brand-500/10');
    });

    zone.addEventListener('dragleave', (e) => {
        e.preventDefault();
        zone.classList.remove('border-brand-500', 'bg-brand-500/10');
    });

    zone.addEventListener('drop', (e) => {
        e.preventDefault();
        zone.classList.remove('border-brand-500', 'bg-brand-500/10');
        if (e.dataTransfer.files.length > 0) {
            uploadFile(e.dataTransfer.files[0]);
        }
    });


    // ── Upload with progress ────────────────────────────────────────
    function uploadFile(file) {
        // Validate file type
        const allowed = ['.pdf', '.docx', '.txt'];
        const ext = '.' + file.name.split('.').pop().toLowerCase();
        if (!allowed.includes(ext)) {
            toast('Invalid file type. Supported: PDF, DOCX, TXT', 'error');
            return;
        }

        // Validate file size (50MB)
        if (file.size > 52428800) {
            toast('File too large. Maximum size is 50 MB.', 'error');
            return;
        }

        // Show progress
        if (progressBar) progressBar.classList.remove('hidden');
        if (filenameEl) filenameEl.textContent = `Uploading ${file.name}…`;
        if (fillBar) fillBar.style.width = '0%';
        if (percentEl) percentEl.textContent = '0%';

        const formData = new FormData();
        formData.append('file', file);

        const xhr = new XMLHttpRequest();
        xhr.open('POST', '/api/documents/upload', true);

        // Track progress
        xhr.upload.addEventListener('progress', (e) => {
            if (e.lengthComputable) {
                const pct = Math.round((e.loaded / e.total) * 100);
                if (fillBar) fillBar.style.width = pct + '%';
                if (percentEl) percentEl.textContent = pct + '%';
            }
        });

        // Success
        xhr.addEventListener('load', () => {
            if (xhr.status === 201 || xhr.status === 200) {
                if (fillBar) fillBar.style.width = '100%';
                if (percentEl) percentEl.textContent = '100%';
                if (filenameEl) filenameEl.textContent = 'Upload complete!';
                toast('Document uploaded successfully!', 'success');
                // Redirect to document page or reload
                try {
                    const data = JSON.parse(xhr.responseText);
                    if (data.id) {
                        setTimeout(() => { window.location.href = `/document/${data.id}`; }, 800);
                        return;
                    }
                } catch {}
                setTimeout(() => location.reload(), 1000);
            } else {
                let msg = 'Upload failed';
                try {
                    const err = JSON.parse(xhr.responseText);
                    msg = err.detail || err.error || msg;
                } catch {}
                toast(msg, 'error');
                if (progressBar) progressBar.classList.add('hidden');
            }
        });

        // Error
        xhr.addEventListener('error', () => {
            toast('Upload failed — network error.', 'error');
            if (progressBar) progressBar.classList.add('hidden');
        });

        xhr.send(formData);
    }
});
