import api from './api';

export const uploadDocument = async (file, onProgress) => {
  const formData = new FormData();
  formData.append('file', file);
  const res = await api.post('/documents/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (e) => onProgress?.(Math.round((e.loaded * 100) / e.total)),
  });
  return res.data;
};

export const getDocuments = async (page = 1, pageSize = 20) => {
  const res = await api.get('/documents', { params: { page, page_size: pageSize } });
  return res.data;
};

export const getDocument = async (id) => {
  const res = await api.get(`/documents/${id}`);
  return res.data;
};

export const getDocumentText = async (id) => {
  const res = await api.get(`/documents/${id}/text`);
  return res.data;
};

export const deleteDocument = async (id) => {
  const res = await api.delete(`/documents/${id}`);
  return res.data;
};
