import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import { getDocument, getDocumentText } from '../services/documentService';
import { analyzeDocument, getAnalysis } from '../services/analysisService';
import DocumentPreview from '../components/Document/DocumentPreview';
import DocumentViewer from '../components/Document/DocumentViewer';
import RiskScore from '../components/Analysis/RiskScore';
import ClauseExtractor from '../components/Analysis/ClauseExtractor';
import ReportGenerator from '../components/Report/ReportGenerator';
import Button from '../components/Common/Button';
import { BarChart3, FileText, Eye } from 'lucide-react';

export default function DocumentPage() {
  const { id } = useParams();
  const [doc, setDoc] = useState(null);
  const [text, setText] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [tab, setTab] = useState('overview');

  useEffect(() => {
    (async () => {
      try {
        const d = await getDocument(id);
        setDoc(d);
        const t = await getDocumentText(id);
        setText(t);
        // Try to load existing analysis
        try { const a = await getAnalysis(id); setAnalysis(a); } catch {}
      } catch (err) { toast.error('Failed to load document'); }
    })();
  }, [id]);

  const handleAnalyze = async () => {
    setAnalyzing(true);
    try {
      const a = await analyzeDocument(id);
      setAnalysis(a);
      toast.success('Analysis complete!');
    } catch (err) { toast.error(err.message || 'Analysis failed'); }
    finally { setAnalyzing(false); }
  };

  if (!doc) return <div className="text-center py-12 text-surface-300">Loading document…</div>;

  const tabs = [
    { key: 'overview', label: 'Overview', icon: Eye },
    { key: 'text', label: 'Full Text', icon: FileText },
    { key: 'analysis', label: 'Analysis', icon: BarChart3 },
  ];

  return (
    <div className="max-w-6xl mx-auto space-y-6 animate-fade-in">
      <DocumentPreview document={doc} />

      {/* Tabs */}
      <div className="flex gap-2 overflow-x-auto pb-1">
        {tabs.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition ${
              tab === t.key ? 'bg-brand-600/20 text-brand-400' : 'text-surface-300 hover:bg-surface-800'
            }`}
          >
            <t.icon size={16} /> {t.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {tab === 'overview' && (
        <div className="grid gap-6 lg:grid-cols-3">
          <div className="lg:col-span-2">
            {analysis ? (
              <div className="glass-card">
                <h3 className="text-lg font-semibold mb-3">Summary</h3>
                <p className="text-sm text-surface-200 whitespace-pre-wrap">{analysis.summary || 'No summary available.'}</p>
                {analysis.recommendations?.length > 0 && (
                  <div className="mt-4">
                    <h4 className="text-sm font-semibold text-surface-100 mb-2">Recommendations</h4>
                    <ul className="space-y-1 text-sm text-surface-300">{analysis.recommendations.map((r, i) => <li key={i}>• {r}</li>)}</ul>
                  </div>
                )}
              </div>
            ) : (
              <div className="glass-card text-center py-10">
                <p className="text-surface-300 mb-4">No analysis yet. Run AI analysis to get insights.</p>
                <Button onClick={handleAnalyze} loading={analyzing} icon={BarChart3}>Analyze Document</Button>
              </div>
            )}
          </div>
          <div className="flex flex-col items-center gap-6">
            {analysis && (
              <>
                <div className="glass-card w-full flex justify-center relative">
                  <RiskScore score={analysis.risk_score || 0} />
                </div>
                <ReportGenerator analysisId={analysis.id} />
              </>
            )}
          </div>
        </div>
      )}

      {tab === 'text' && <DocumentViewer text={text?.cleaned_text || text?.raw_text} filename={doc.filename} />}

      {tab === 'analysis' && (
        <div className="space-y-6">
          {!analysis && (
            <div className="glass-card text-center py-8">
              <Button onClick={handleAnalyze} loading={analyzing} icon={BarChart3}>Run Analysis</Button>
            </div>
          )}
          {analysis && <ClauseExtractor clauses={analysis.clauses} />}
        </div>
      )}
    </div>
  );
}
