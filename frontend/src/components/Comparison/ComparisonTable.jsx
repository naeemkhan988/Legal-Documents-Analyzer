import React from 'react';

export default function ComparisonTable({ clauseComparison = {} }) {
  const types = Object.keys(clauseComparison);
  if (!types.length) return null;

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm text-left">
        <thead className="text-xs uppercase text-surface-300 border-b border-white/5">
          <tr><th className="px-4 py-3">Clause Type</th><th className="px-4 py-3">Present in All</th><th className="px-4 py-3">Summary</th></tr>
        </thead>
        <tbody>
          {types.map((t) => {
            const info = clauseComparison[t];
            return (
              <tr key={t} className="border-b border-white/5 hover:bg-surface-800/50 transition">
                <td className="px-4 py-3 font-medium capitalize">{t.replace(/_/g, ' ')}</td>
                <td className="px-4 py-3">{info.present_in_all ? <span className="badge-green">Yes</span> : <span className="badge-red">No</span>}</td>
                <td className="px-4 py-3 text-surface-300">{info.summary}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
