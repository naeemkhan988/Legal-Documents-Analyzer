import api from './api';

export const searchDocuments = async (query, topK = 5) => {
  const res = await api.post('/search', { query, top_k: topK });
  return res.data;
};

export const searchWithinDocument = async (documentId, query, topK = 5) => {
  const res = await api.post(`/search/${documentId}`, { query, top_k: topK });
  return res.data;
};

export const ragAnswer = async (query, documentId = null) => {
  const res = await api.post('/search/rag-answer', { query, document_id: documentId });
  return res.data;
};

export const getSearchHistory = async () => {
  const res = await api.get('/search/history');
  return res.data;
};
