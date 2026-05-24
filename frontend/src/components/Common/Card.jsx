import React from 'react';

export default function Card({ children, className = '', hover = true, onClick }) {
  return (
    <div
      className={`glass-card ${hover ? 'cursor-pointer' : ''} ${className}`}
      onClick={onClick}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
    >
      {children}
    </div>
  );
}

export function CardHeader({ children, className = '' }) {
  return <div className={`mb-4 ${className}`}>{children}</div>;
}

export function CardTitle({ children, className = '' }) {
  return <h3 className={`text-lg font-semibold text-surface-50 ${className}`}>{children}</h3>;
}

export function CardContent({ children, className = '' }) {
  return <div className={className}>{children}</div>;
}
