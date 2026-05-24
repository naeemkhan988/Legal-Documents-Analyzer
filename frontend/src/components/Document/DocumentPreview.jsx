import React from 'react';
import { FileText, Calendar, HardDrive } from 'lucide-react';

export default function DocumentPreview({ document }) {
  if (!document) return null;
  return (
    <div className="glass-card">
      <div className="flex items-start gap-4">
        <div className="w-12 h-12 rounded-xl bg-brand-600/20 flex items-center justify-center flex-shrink-0">
          <FileText size={22} className="text-brand-400" />
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-surface-50 truncate">{document.filename}</h3>
          <div className="flex flex-wrap gap-4 mt-2 text-xs text-surface-300">
            <span className="flex items-center gap-1"><HardDrive size={12} /> {(document.file_size / 1024).toFixed(1)} KB</span>
            <span className="flex items-center gap-1"><Calendar size={12} /> {new Date(document.created_at).toLocaleString()}</span>
            <span className="badge bg-surface-800 text-surface-300 uppercase">{document.file_type}</span>
          </div>
        </div>
      </div>
      {document.cleaned_text && (
        <p className="mt-4 text-sm text-surface-300 line-clamp-4">{document.cleaned_text.slice(0, 400)}…</p>
      )}
    </div>
  );
}
