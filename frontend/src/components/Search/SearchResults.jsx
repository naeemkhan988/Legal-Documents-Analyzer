import React from 'react';

export default function SearchResults({ results = [], query }) {
  if (!results.length) return <div className="text-surface-300 text-sm text-center py-8">No results found{query ? ` for "${query}"` : ''}.</div>;

  return (
    <div className="space-y-3">
      {results.map((r, i) => (
        <div key={i} className="glass-card !p-4 animate-slide-up" style={{ animationDelay: `${i * 50}ms` }}>
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium text-brand-400">Result #{i + 1}</span>
            <span className="badge bg-surface-800 text-surface-300">{(r.score * 100).toFixed(1)}% match</span>
          </div>
          <p className="text-sm text-surface-200">{r.text}</p>
        </div>
      ))}
    </div>
  );
}
