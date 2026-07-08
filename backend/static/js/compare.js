/**
 * compare.js — Compare Page Interactions
 * =========================================
 * Submit selected document IDs for comparison, render results.
 */

// ── Run Comparison ──────────────────────────────────────────────────
async function runComparison() {
    const docA = document.getElementById('doc-a')?.value;
    const docB = document.getElementById('doc-b')?.value;

    if (!docA || !docB) {
        toast('Please select two documents to compare.', 'error');
        return;
    }
    if (docA === docB) {
        toast('Please select two different documents.', 'error');
        return;
    }

    const spinner = document.getElementById('compare-spinner');
    const btn = document.getElementById('compare-btn');
    const resultsDiv = document.getElementById('compare-results');

    // Show loading
    if (spinner) spinner.classList.remove('hidden');
    if (btn) btn.disabled = true;

    try {
        const data = await fetchJSON('/api/compare', {
            method: 'POST',
            body: JSON.stringify({ document_ids: [docA, docB] }),
        });

        toast('Comparison complete!', 'success');
        renderComparison(data);
    } catch (err) {
        toast(err.message || 'Comparison failed', 'error');
    } finally {
        if (spinner) spinner.classList.add('hidden');
        if (btn) btn.disabled = false;
    }
}


// ── Render Comparison Results ───────────────────────────────────────
function renderComparison(data) {
    const resultsDiv = document.getElementById('compare-results');
    const summaryText = document.getElementById('compare-summary-text');
    const diffContent = document.getElementById('compare-diff-content');

    if (!resultsDiv) return;
    resultsDiv.classList.remove('hidden');

    // Summary
    const result = data.comparison_result || {};
    if (summaryText) {
        summaryText.textContent = result.summary || 'No summary generated.';
    }

    // Differences
    if (diffContent) {
        const diffs = data.differences || result.differences;
        if (diffs && typeof diffs === 'object') {
            let html = '';
            if (Array.isArray(diffs)) {
                // Array of difference items
                diffs.forEach((diff, i) => {
                    html += `
                        <div class="glass-card" style="padding: 0.75rem 1rem;">
                            <p class="text-sm text-surface-200">${escapeHtml(typeof diff === 'string' ? diff : JSON.stringify(diff, null, 2))}</p>
                        </div>
                    `;
                });
            } else {
                // Object with keys
                for (const [key, val] of Object.entries(diffs)) {
                    html += `
                        <div class="glass-card" style="padding: 0.75rem 1rem;">
                            <span class="badge badge-blue mb-2">${escapeHtml(key)}</span>
                            <p class="text-sm text-surface-200 mt-1 whitespace-pre-wrap">${escapeHtml(typeof val === 'string' ? val : JSON.stringify(val, null, 2))}</p>
                        </div>
                    `;
                }
            }
            diffContent.innerHTML = html || '<p class="text-sm text-surface-300">No differences found.</p>';
        } else {
            diffContent.innerHTML = '<p class="text-sm text-surface-300">No structured differences available.</p>';
        }
    }
}


// ── HTML Escape Helper ──────────────────────────────────────────────
function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}
