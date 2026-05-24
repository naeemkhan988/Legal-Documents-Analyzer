import React from 'react';
import RiskIndicator from './RiskIndicator';

export default function ClauseCard({ clause }) {
  const typeLabel = (clause.clause_type || '').replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());

  return (
    <div className="glass-card !p-4">
      <div className="flex items-start justify-between gap-3 mb-2">
        <span className="text-xs font-semibold text-brand-400 uppercase tracking-wide">{typeLabel}</span>
        <RiskIndicator level={clause.risk_level} />
      </div>
      <p className="text-sm text-surface-200 line-clamp-3 mb-2">{clause.text}</p>
      <div className="flex items-center justify-between text-xs text-surface-300">
        <span>Confidence: {(clause.confidence * 100).toFixed(0)}%</span>
        {clause.suggested_change && <span className="text-yellow-400 truncate max-w-[50%]">💡 {clause.suggested_change}</span>}
      </div>
    </div>
  );
}
