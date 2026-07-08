/**
 * document.js — Document Page Interactions
 * ==========================================
 * Tab switching, analyze document, generate reports, delete + redirect.
 */

// ── Tab Switching ───────────────────────────────────────────────────
function switchTab(tabName) {
    // Deactivate all tabs
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(panel => panel.classList.remove('active'));

    // Activate selected tab
    const btn = document.querySelector(`.tab-btn[data-tab="${tabName}"]`);
    const panel = document.getElementById(`tab-${tabName}`);
    if (btn) btn.classList.add('active');
    if (panel) panel.classList.add('active');
}


// ── Analyze Document ────────────────────────────────────────────────
async function analyzeDocument() {
    const page = document.getElementById('doc-page');
    if (!page) return;
    const docId = page.dataset.docId;

    // Disable buttons and show spinner
    const buttons = document.querySelectorAll('[onclick*="analyzeDocument"]');
    buttons.forEach(btn => {
        btn.disabled = true;
        btn.innerHTML = '<div class="spinner"></div> Analyzing…';
    });

    try {
        const data = await fetchJSON(`/api/analyze/${docId}`, { method: 'POST' });
        toast('Analysis complete!', 'success');
        // Reload the page to show the results server-rendered
        setTimeout(() => location.reload(), 500);
    } catch (err) {
        toast(err.message || 'Analysis failed', 'error');
        buttons.forEach(btn => {
            btn.disabled = false;
            btn.innerHTML = '<i data-lucide="bar-chart-3" class="w-4 h-4"></i> Analyze Document';
            lucide.createIcons();
        });
    }
}


// ── Generate Report ─────────────────────────────────────────────────
async function generateReport(analysisId, reportType) {
    const resultDiv = document.getElementById('report-result');

    try {
        toast(`Generating ${reportType.toUpperCase()} report…`, 'info');
        const data = await fetchJSON(`/api/reports/${analysisId}`, {
            method: 'POST',
            body: JSON.stringify({ report_type: reportType }),
        });
        toast(`${reportType.toUpperCase()} report ready!`, 'success');

        // Show download link
        if (resultDiv) {
            resultDiv.classList.remove('hidden');
            resultDiv.innerHTML = `
                <a href="/api/reports/${data.id}/download"
                   class="btn-primary text-sm flex items-center gap-2 w-full justify-center"
                   target="_blank">
                    <i data-lucide="download" class="w-4 h-4"></i>
                    Download ${reportType.toUpperCase()} Report
                </a>
            `;
            lucide.createIcons();
        }
    } catch (err) {
        toast(err.message || 'Report generation failed', 'error');
    }
}


// ── Delete Document and Redirect ────────────────────────────────────
async function deleteDocumentAndRedirect(docId) {
    if (!confirm('Delete this document and all associated data? This cannot be undone.')) return;

    try {
        await fetchJSON(`/api/documents/${docId}`, { method: 'DELETE' });
        toast('Document deleted', 'success');
        setTimeout(() => { window.location.href = '/'; }, 500);
    } catch (err) {
        toast(err.message || 'Delete failed', 'error');
    }
}
