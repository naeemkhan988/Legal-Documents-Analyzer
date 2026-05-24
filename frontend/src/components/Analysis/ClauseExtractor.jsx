import React from 'react';
import ClauseCard from './ClauseCard';

export default function ClauseExtractor({ clauses = [] }) {
  if (!clauses.length) return <div className="text-surface-300 text-sm">No clauses extracted yet.</div>;

  const grouped = clauses.reduce((acc, c) => {
    const t = c.clause_type || 'unknown';
    (acc[t] = acc[t] || []).push(c);
    return acc;
  }, {});

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-surface-50">Extracted Clauses</h3>
        <span className="badge bg-surface-800 text-surface-300">{clauses.length} found</span>
      </div>
      {Object.entries(grouped).map(([type, items]) => (
        <div key={type}>
          <h4 className="text-sm font-medium text-surface-300 mb-2 uppercase tracking-wide">{type.replace(/_/g, ' ')}</h4>
          <div className="grid gap-3 md:grid-cols-2">
            {items.map((c, i) => <ClauseCard key={i} clause={c} />)}
          </div>
        </div>
      ))}
    </div>
  );
}
