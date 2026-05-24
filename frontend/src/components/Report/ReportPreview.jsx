import React from 'react';
import { FileText, Download, Calendar } from 'lucide-react';

export default function ReportPreview({ reports = [] }) {
  if (!reports.length) return <div className="text-surface-300 text-sm text-center py-8">No reports generated yet.</div>;

  return (
    <div className="space-y-3">
      {reports.map((r) => (
        <div key={r.id} className="glass-card !p-4 flex items-center gap-4">
          <div className="w-10 h-10 rounded-xl bg-brand-600/20 flex items-center justify-center">
            <FileText size={18} className="text-brand-400" />
          </div>
          <div className="flex-1">
            <p className="text-sm font-medium">{r.report_type.toUpperCase()} Report</p>
            <p className="text-xs text-surface-300 flex items-center gap-1"><Calendar size={12} /> {new Date(r.created_at).toLocaleString()}</p>
          </div>
          <a href={`/api/reports/${r.id}/download`} className="p-2 rounded-lg hover:bg-surface-800 transition" title="Download">
            <Download size={16} className="text-brand-400" />
          </a>
        </div>
      ))}
    </div>
  );
}
