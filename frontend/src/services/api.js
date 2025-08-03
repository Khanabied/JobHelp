import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
});

// Add auth header to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('authToken');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle auth errors globally
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('authToken');
      window.location.href = '/auth';
    }
    return Promise.reject(error);
  }
);

// Auth service
export const authService = {
  async login(email, password) {
    const response = await api.post('/api/auth/login', { email, password });
    return response.data;
  },

  async register(email, password, full_name) {
    const response = await api.post('/api/auth/register', { 
      email, 
      password, 
      full_name 
    });
    return response.data;
  },

  async getMe() {
    const response = await api.get('/api/auth/me');
    return response.data;
  }
};

// File service
export const fileService = {
  async uploadResume(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await api.post('/api/upload/resume', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  async cleanupFile(fileId) {
    const response = await api.delete(`/api/cleanup/${fileId}`);
    return response.data;
  }
};

// Analysis service
export const analysisService = {
  async analyzeJob(jobData) {
    const response = await api.post('/api/analyze/job', jobData);
    return response.data;
  },

  async getAnalysisResults(analysisId) {
    const response = await api.get(`/api/analysis/results/${analysisId}`);
    return response.data;
  },

  async downloadFile(analysisId, fileType) {
    const response = await api.get(`/api/analysis/download/${analysisId}/${fileType}`);
    return response.data;
  }
};

// General API service
export const apiService = {
  async get(endpoint) {
    const response = await api.get(endpoint);
    return response.data;
  },

  async post(endpoint, data) {
    const response = await api.post(endpoint, data);
    return response.data;
  }
};

export default api;