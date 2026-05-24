import React from 'react';

export default function RiskScore({ score, size = 'lg' }) {
  const level = score >= 70 ? 'RED' : score >= 40 ? 'YELLOW' : 'GREEN';
  const color = { RED: '#ef4444', YELLOW: '#eab308', GREEN: '#22c55e' }[level];
  const dim = size === 'lg' ? 140 : 80;
  const stroke = size === 'lg' ? 10 : 6;
  const r = (dim - stroke) / 2;
  const circ = 2 * Math.PI * r;
  const offset = circ - (score / 100) * circ;

  return (
    <div className="flex flex-col items-center gap-2">
      <svg width={dim} height={dim} className="-rotate-90">
        <circle cx={dim/2} cy={dim/2} r={r} fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth={stroke} />
        <circle cx={dim/2} cy={dim/2} r={r} fill="none" stroke={color} strokeWidth={stroke} strokeLinecap="round" strokeDasharray={circ} strokeDashoffset={offset} className="transition-all duration-1000" />
      </svg>
      <div className="absolute flex flex-col items-center" style={{ marginTop: dim * 0.3 }}>
        <span className="text-3xl font-bold" style={{ color }}>{Math.round(score)}</span>
        <span className="text-xs text-surface-300">/ 100</span>
      </div>
      <span className={`badge ${level === 'RED' ? 'badge-red' : level === 'YELLOW' ? 'badge-yellow' : 'badge-green'}`}>
        {level} RISK
      </span>
    </div>
  );
}
