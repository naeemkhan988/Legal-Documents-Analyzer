/**
 * API Service — Axios instance with interceptors
 */
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120_000,
  headers: { 'Content-Type': 'application/json' },
});

// Request interceptor — attach auth token if present
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('legalrag_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Response interceptor — normalise errors
api.interceptors.response.use(
  (res) => res,
  (err) => {
    const message =
      err.response?.data?.error ||
      err.response?.data?.detail ||
      err.message ||
      'Network error';
    return Promise.reject({ message, status: err.response?.status });
  }
);

export default api;
