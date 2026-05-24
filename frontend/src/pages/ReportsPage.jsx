import React, { useEffect, useState } from 'react';
import { getReports } from '../services/reportService';
import ReportPreview from '../components/Report/ReportPreview';

export default function ReportsPage() {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try { const data = await getReports(); setReports(data.items || []); }
      catch {}
      finally { setLoading(false); }
    })();
  }, []);

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-in">
      <h1 className="text-2xl font-bold gradient-text">Reports</h1>
      {loading ? <div className="glass-card animate-pulse h-40" /> : <ReportPreview reports={reports} />}
    </div>
  );
}
