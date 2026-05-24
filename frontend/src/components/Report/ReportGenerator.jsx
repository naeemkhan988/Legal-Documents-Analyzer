import React, { useState } from 'react';
import { Download, FileText } from 'lucide-react';
import Button from '../Common/Button';
import { generateReport, downloadReport } from '../../services/reportService';
import { toast } from 'react-hot-toast';

const FORMATS = [
  { value: 'pdf',   label: 'PDF Report' },
  { value: 'html',  label: 'HTML Report' },
  { value: 'json',  label: 'JSON Export' },
  { value: 'excel', label: 'Excel Export' },
];

export default function ReportGenerator({ analysisId }) {
  const [format, setFormat] = useState('pdf');
  const [loading, setLoading] = useState(false);

  const handleGenerate = async () => {
    setLoading(true);
    try {
      const report = await generateReport(analysisId, format);
      toast.success('Report generated!');
      // Auto download
      const blob = await downloadReport(report.id);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `report.${format === 'excel' ? 'xlsx' : format}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) { toast.error(err.message); }
    finally { setLoading(false); }
  };

  if (!analysisId) return null;

  return (
    <div className="glass-card">
      <h3 className="text-lg font-semibold mb-3 flex items-center gap-2"><FileText size={18} className="text-brand-400" /> Generate Report</h3>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-4">
        {FORMATS.map((f) => (
          <button
            key={f.value}
            onClick={() => setFormat(f.value)}
            className={`p-3 rounded-xl text-sm border transition ${format === f.value ? 'border-brand-500 bg-brand-500/10 text-brand-400' : 'border-surface-700 text-surface-300 hover:border-surface-600'}`}
          >
            {f.label}
          </button>
        ))}
      </div>
      <Button onClick={handleGenerate} loading={loading} icon={Download}>Download {format.toUpperCase()}</Button>
    </div>
  );
}
