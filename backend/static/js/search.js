/**
 * search.js — Search Page Interactions
 * =======================================
 * Mode toggle (Search / RAG), submit query, render results.
 */

let searchMode = 'search';  // 'search' or 'rag'

// ── Set Search Mode ─────────────────────────────────────────────────
function setSearchMode(mode) {
    searchMode = mode;

    // Update button states
    document.getElementById('mode-search').classList.toggle('active', mode === 'search');
    document.getElementById('mode-rag').classList.toggle('active', mode === 'rag');

    // Update placeholder
    const input = document.getElementById('search-input');
    if (input) {
        input.placeholder = mode === 'rag'
            ? 'Ask a question about your contracts…'
            : 'Search across all documents…';
    }

    // Clear previous results
    document.getElementById('rag-answer').classList.add('hidden');
}


// ── Handle Search ───────────────────────────────────────────────────
async function handleSearch(event) {
    event.preventDefault();
    const input = document.getElementById('search-input');
    const query = input ? input.value.trim() : '';
    if (!query) return;

    const spinner = document.getElementById('search-spinner');
    const searchBtn = document.getElementById('search-btn');
    const resultsDiv = document.getElementById('search-results');
    const emptyDiv = document.getElementById('search-empty');
    const ragDiv = document.getElementById('rag-answer');
    const ragText = document.getElementById('rag-answer-text');

    // Show loading
    if (spinner) spinner.classList.remove('hidden');
    if (searchBtn) searchBtn.disabled = true;
    if (emptyDiv) emptyDiv.classList.add('hidden');

    try {
        if (searchMode === 'rag') {
            // RAG pipeline
            const data = await fetchJSON('/api/search/rag-answer', {
                method: 'POST',
                body: JSON.stringify({ query }),
            });

            // Show AI answer
            if (ragDiv && ragText) {
                ragText.textContent = data.answer || 'No answer generated.';
                ragDiv.classList.remove('hidden');
            }

            // Show sources as results
            renderResults(resultsDiv, data.sources || [], query);
        } else {
            // Semantic search
            const data = await fetchJSON('/api/search', {
                method: 'POST',
                body: JSON.stringify({ query }),
            });

            if (ragDiv) ragDiv.classList.add('hidden');
            renderResults(resultsDiv, data.results || [], query);
        }
    } catch (err) {
        toast(err.message || 'Search failed', 'error');
    } finally {
        if (spinner) spinner.classList.add('hidden');
        if (searchBtn) searchBtn.disabled = false;
    }
}


// ── Render Search Results ───────────────────────────────────────────
function renderResults(container, results, query) {
    if (!container) return;

    if (results.length === 0) {
        container.innerHTML = `
            <div class="glass-card text-center py-8">
                <p class="text-surface-300">No results found for "${query}".</p>
            </div>
        `;
        return;
    }

    container.innerHTML = `
        <h3 class="text-sm font-semibold text-surface-300 mb-2">${results.length} result${results.length !== 1 ? 's' : ''}</h3>
        ${results.map((r, i) => `
            <div class="glass-card animate-slide-up" style="padding: 1rem 1.5rem; animation-delay: ${i * 50}ms;">
                <div class="flex items-center justify-between mb-2">
                    <span class="badge badge-blue">Score: ${(r.score || 0).toFixed(3)}</span>
                    ${r.document_id ? `<a href="/document/${r.document_id}" class="text-xs text-brand-400 hover:underline">View Document →</a>` : ''}
                </div>
                <p class="text-sm text-surface-200">${escapeHtml(r.text || '')}</p>
            </div>
        `).join('')}
    `;
}


// ── HTML Escape Helper ──────────────────────────────────────────────
function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}
