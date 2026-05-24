import React, { useState } from 'react';
import { GitCompare } from 'lucide-react';
import Button from '../Common/Button';
import { compareDocuments } from '../../services/reportService';
import { toast } from 'react-hot-toast';

export default function ContractComparator({ documents = [] }) {
  const [selected, setSelected] = useState([]);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const toggle = (id) => {
    setSelected((prev) => prev.includes(id) ? prev.filter((x) => x !== id) : prev.length < 2 ? [...prev, id] : prev);
  };

  const handleCompare = async () => {
    if (selected.length < 2) { toast.error('Select at least 2 documents'); return; }
    setLoading(true);
    try {
      const data = await compareDocuments(selected);
      setResult(data);
    } catch (err) { toast.error(err.message); }
    finally { setLoading(false); }
  };

  return (
    <div className="space-y-4">
      <div className="glass-card">
        <h3 className="text-lg font-semibold mb-3">Select Documents to Compare</h3>
        <div className="grid gap-2 sm:grid-cols-2">
          {documents.map((d) => (
            <button
              key={d.id}
              onClick={() => toggle(d.id)}
              className={`p-3 rounded-xl text-left text-sm border transition ${
                selected.includes(d.id) ? 'border-brand-500 bg-brand-500/10' : 'border-surface-700 hover:border-surface-600'
              }`}
            >
              {d.filename}
            </button>
          ))}
        </div>
        <Button onClick={handleCompare} loading={loading} icon={GitCompare} className="mt-4">Compare ({selected.length}/2)</Button>
      </div>

      {result && (
        <div className="glass-card animate-fade-in">
          <h3 className="text-lg font-semibold mb-3">Comparison Result</h3>
          <div className="grid gap-4 sm:grid-cols-3 text-center">
            <div><p className="text-2xl font-bold text-brand-400">{((result.comparison_result?.similarity_score || 0) * 100).toFixed(1)}%</p><p className="text-xs text-surface-300">Similarity</p></div>
            <div><p className="text-2xl font-bold text-yellow-400">{result.differences?.total_changes || 0}</p><p className="text-xs text-surface-300">Changes</p></div>
            <div><p className="text-2xl font-bold text-green-400">{result.differences?.added_lines || 0}</p><p className="text-xs text-surface-300">Added Lines</p></div>
          </div>
          {result.comparison_result?.summary && <p className="mt-4 text-sm text-surface-300 whitespace-pre-wrap">{result.comparison_result.summary}</p>}
        </div>
      )}
    </div>
  );
}
