/**
 * API client for RecoverAI backend.
 * Connects via Vite proxy in dev (/api -> http://127.0.0.1:8000/api).
 */

const API_BASE = (import.meta.env?.VITE_API_BASE_URL || '/api').replace(/\/$/, '');

async function request(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

// Payments
export const getPayments = (params = {}) => {
  const query = new URLSearchParams(
    Object.entries(params).filter(([_, v]) => v !== undefined && v !== null && v !== '')
  ).toString();
  return request(`/payments${query ? `?${query}` : ''}`);
};

export const getPayment = (id) => request(`/payments/${id}`);

export const getDemoCases = () => request('/payments/demo-cases');

export const seedPayments = () => request('/payments/seed', { method: 'POST' });

// Analysis
export const analyzePayment = (paymentId) =>
  request(`/analyze/${paymentId}`, { method: 'POST' });

// Batch
export const runBatch = () => request('/batch/run', { method: 'POST' });

export const getBatches = () => request('/batch');

export const getBatch = (batchId) => request(`/batch/${batchId}`);

export const getBatchResults = (batchId, params = {}) => {
  const query = new URLSearchParams(
    Object.entries(params).filter(([_, v]) => v !== undefined && v !== null && v !== '')
  ).toString();
  return request(`/batch/${batchId}/results${query ? `?${query}` : ''}`);
};

// Dashboard
export const getDashboardStats = () => request('/dashboard/stats');

// Audit
export const getAuditLogs = (params = {}) => {
  const query = new URLSearchParams(
    Object.entries(params).filter(([_, v]) => v !== undefined && v !== null && v !== '')
  ).toString();
  return request(`/audit${query ? `?${query}` : ''}`);
};

export const getPaymentAudit = (paymentId) =>
  request(`/audit/payment/${paymentId}`);

// System Status & Policy Configuration
export const getSystemStatus = () => request('/system/status');

