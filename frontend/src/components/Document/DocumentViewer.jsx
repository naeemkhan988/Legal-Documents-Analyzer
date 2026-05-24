import React from 'react';
import { FileText } from 'lucide-react';

export default function DocumentViewer({ text, filename }) {
  if (!text) return <div className="glass-card text-surface-300 text-center py-12">No text available</div>;

  return (
    <div className="glass-card max-h-[600px] overflow-y-auto">
      <div className="flex items-center gap-2 mb-4 pb-3 border-b border-white/5">
        <FileText size={18} className="text-brand-400" />
        <span className="text-sm font-medium text-surface-200">{filename}</span>
        <span className="ml-auto text-xs text-surface-300">{text.length.toLocaleString()} chars</span>
      </div>
      <pre className="text-sm text-surface-200 whitespace-pre-wrap font-mono leading-relaxed">{text}</pre>
    </div>
  );
}
