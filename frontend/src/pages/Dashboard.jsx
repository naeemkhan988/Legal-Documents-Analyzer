import React, { useEffect, useState } from 'react';
import { FileText, BarChart3, ShieldAlert, Search } from 'lucide-react';
import DocumentUpload from '../components/Document/DocumentUpload';
import DocumentList from '../components/Document/DocumentList';
import useDocuments from '../hooks/useDocuments';
import Card from '../components/Common/Card';
import { toast } from 'react-hot-toast';

export default function Dashboard() {
  const { documents, total, loading, fetchDocuments, removeDocument } = useDocuments();

  const handleUploadComplete = () => {
    fetchDocuments(1);
  };

  const handleDelete = async (id) => {
    try {
      await removeDocument(id);
      toast.success('Document deleted');
    } catch { toast.error('Delete failed'); }
  };

  const stats = [
    { label: 'Documents', value: total, icon: FileText, color: 'text-brand-400' },
    { label: 'Analyzed', value: '—', icon: BarChart3, color: 'text-green-400' },
    { label: 'High Risk', value: '—', icon: ShieldAlert, color: 'text-red-400' },
    { label: 'Searches', value: '—', icon: Search, color: 'text-yellow-400' },
  ];

  return (
    <div className="space-y-6 max-w-6xl mx-auto animate-fade-in">
      {/* Hero */}
      <div className="glass-card !p-8 text-center">
        <h1 className="text-3xl md:text-4xl font-bold mb-2">
          <span className="gradient-text">Legal Document Analyzer</span>
        </h1>
        <p className="text-surface-300 max-w-lg mx-auto">Upload contracts, extract clauses, score risks, and get AI-powered insights — all in one place.</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {stats.map((s) => (
          <Card key={s.label} hover={false} className="!p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-surface-800 flex items-center justify-center">
              <s.icon size={18} className={s.color} />
            </div>
            <div>
              <p className="text-xl font-bold">{s.value}</p>
              <p className="text-xs text-surface-300">{s.label}</p>
            </div>
          </Card>
        ))}
      </div>

      {/* Upload */}
      <DocumentUpload onUploadComplete={handleUploadComplete} />

      {/* Recent Documents */}
      <div>
        <h2 className="text-lg font-semibold mb-3">Recent Documents</h2>
        <DocumentList documents={documents} onDelete={handleDelete} loading={loading} />
      </div>
    </div>
  );
}
