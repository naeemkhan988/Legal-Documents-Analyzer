import { useState, useCallback, useEffect } from 'react';
import { getDocuments, deleteDocument as deleteDocApi } from '../services/documentService';

export default function useDocuments() {
  const [documents, setDocuments] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);

  const fetchDocuments = useCallback(async (p = page) => {
    setLoading(true);
    try {
      const data = await getDocuments(p);
      setDocuments(data.items || []);
      setTotal(data.total || 0);
    } catch { /* handled by interceptor */ }
    finally { setLoading(false); }
  }, [page]);

  useEffect(() => { fetchDocuments(); }, [fetchDocuments]);

  const removeDocument = useCallback(async (id) => {
    await deleteDocApi(id);
    setDocuments((prev) => prev.filter((d) => d.id !== id));
    setTotal((prev) => prev - 1);
  }, []);

  return { documents, total, loading, page, setPage, fetchDocuments, removeDocument };
}
