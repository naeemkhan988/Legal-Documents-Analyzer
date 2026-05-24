import api from './api';

export const analyzeDocument = async (documentId) => {
  const res = await api.post(`/analyze/${documentId}`);
  return res.data;
};

export const getAnalysis = async (documentId) => {
  const res = await api.get(`/analyze/${documentId}`);
  return res.data;
};

export const extractClauses = async (documentId) => {
  const res = await api.post(`/analyze/${documentId}/clauses`);
  return res.data;
};

export const extractEntities = async (documentId) => {
  const res = await api.post(`/analyze/${documentId}/entities`);
  return res.data;
};

export const getRiskScore = async (documentId) => {
  const res = await api.post(`/analyze/${documentId}/risk-score`);
  return res.data;
};

export const getSummary = async (documentId) => {
  const res = await api.post(`/analyze/${documentId}/summary`);
  return res.data;
};
