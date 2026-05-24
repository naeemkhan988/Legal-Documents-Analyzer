import { useState, useCallback } from 'react';
import { analyzeDocument, getAnalysis } from '../services/analysisService';

export default function useAnalysis() {
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const runAnalysis = useCallback(async (documentId) => {
    setLoading(true);
    setError(null);
    try {
      const data = await analyzeDocument(documentId);
      setAnalysis(data);
      return data;
    } catch (err) {
      setError(err.message || 'Analysis failed');
      throw err;
    } finally { setLoading(false); }
  }, []);

  const fetchAnalysis = useCallback(async (documentId) => {
    setLoading(true);
    try {
      const data = await getAnalysis(documentId);
      setAnalysis(data);
    } catch { setAnalysis(null); }
    finally { setLoading(false); }
  }, []);

  return { analysis, loading, error, runAnalysis, fetchAnalysis };
}
