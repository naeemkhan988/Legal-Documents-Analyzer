import React from 'react';

export default function RiskIndicator({ level, className = '' }) {
  const config = {
    RED:    { bg: 'bg-red-500',    ring: 'ring-red-500/30',    text: 'text-red-400',    label: 'High Risk' },
    YELLOW: { bg: 'bg-yellow-500', ring: 'ring-yellow-500/30', text: 'text-yellow-400', label: 'Medium Risk' },
    GREEN:  { bg: 'bg-green-500',  ring: 'ring-green-500/30',  text: 'text-green-400',  label: 'Low Risk' },
  }[level] || { bg: 'bg-surface-500', ring: '', text: 'text-surface-400', label: 'Unknown' };

  return (
    <span className={`inline-flex items-center gap-1.5 ${className}`}>
      <span className={`w-2.5 h-2.5 rounded-full ${config.bg} ring-4 ${config.ring}`} />
      <span className={`text-xs font-medium ${config.text}`}>{config.label}</span>
    </span>
  );
}
