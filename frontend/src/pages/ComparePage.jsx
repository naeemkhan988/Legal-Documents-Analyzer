import React from 'react';
import ContractComparator from '../components/Comparison/ContractComparator';
import useDocuments from '../hooks/useDocuments';

export default function ComparePage() {
  const { documents, loading } = useDocuments();

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-in">
      <h1 className="text-2xl font-bold gradient-text">Compare Contracts</h1>
      <p className="text-surface-300 text-sm">Select two documents to compare clauses, risk levels, and content differences.</p>
      {loading ? <div className="glass-card animate-pulse h-40" /> : <ContractComparator documents={documents} />}
    </div>
  );
}
