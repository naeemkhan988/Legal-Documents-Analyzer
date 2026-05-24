import React from 'react';

const variants = {
  primary:   'btn-primary',
  secondary: 'btn-secondary',
  danger:    'btn-danger',
};

export default function Button({ children, variant = 'primary', className = '', icon: Icon, loading, ...props }) {
  return (
    <button className={`${variants[variant] || variants.primary} inline-flex items-center gap-2 ${className}`} disabled={loading || props.disabled} {...props}>
      {loading ? (
        <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" /></svg>
      ) : Icon ? <Icon size={16} /> : null}
      {children}
    </button>
  );
}
