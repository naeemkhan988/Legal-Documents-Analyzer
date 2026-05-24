import api from './api';

export const generateReport = async (analysisId, reportType = 'pdf') => {
  const res = await api.post(`/reports/${analysisId}`, { report_type: reportType });
  return res.data;
};

export const downloadReport = async (reportId) => {
  const res = await api.get(`/reports/${reportId}/download`, { responseType: 'blob' });
  return res.data;
};

export const getReports = async (page = 1) => {
  const res = await api.get('/reports', { params: { page } });
  return res.data;
};

export const compareDocuments = async (documentIds) => {
  const res = await api.post('/compare', { document_ids: documentIds });
  return res.data;
};
