import React from 'react';
import { useNavigate } from 'react-router-dom';
import { FileText, Trash2, BarChart3 } from 'lucide-react';
import Button from '../Common/Button';

const TYPE_COLORS = { pdf: 'text-red-400', docx: 'text-blue-400', txt: 'text-green-400' };

export default function DocumentList({ documents, onDelete, loading }) {
  const navigate = useNavigate();

  if (loading) return <div className="glass-card animate-pulse h-40" />;
  if (!documents?.length) return <div className="glass-card text-center py-10 text-surface-300">No documents uploaded yet.</div>;

  return (
    <div className="space-y-3">
      {documents.map((doc) => (
        <div key={doc.id} className="glass-card flex items-center gap-4 hover:border-brand-500/30 transition group" onClick={() => navigate(`/document/${doc.id}`)}>
          <div className="w-10 h-10 rounded-xl bg-surface-800 flex items-center justify-center">
            <FileText size={18} className={TYPE_COLORS[doc.file_type] || 'text-surface-300'} />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-surface-100 truncate">{doc.filename}</p>
            <p className="text-xs text-surface-300">{(doc.file_size / 1024).toFixed(1)} KB · {new Date(doc.created_at).toLocaleDateString()}</p>
          </div>
          <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition">
            <button onClick={(e) => { e.stopPropagation(); navigate(`/document/${doc.id}`); }} className="p-2 rounded-lg hover:bg-surface-800" title="Analyze">
              <BarChart3 size={16} className="text-brand-400" />
            </button>
            <button onClick={(e) => { e.stopPropagation(); onDelete?.(doc.id); }} className="p-2 rounded-lg hover:bg-red-500/10" title="Delete">
              <Trash2 size={16} className="text-red-400" />
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
