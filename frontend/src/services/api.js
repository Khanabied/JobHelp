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

  async analyzeJobExtended(jobData) {
    const response = await api.post('/api/analyze/extended', jobData);
    return response.data;
  },

  async generateCoverLetter(jobData) {
    const response = await api.post('/api/agents/cover-letter', jobData);
    return response.data;
  },

  async optimizeLinkedIn(jobData) {
    const response = await api.post('/api/agents/linkedin', jobData);
    return response.data;
  },

  async prepareInterview(jobData) {
    const response = await api.post('/api/agents/interview', jobData);
    return response.data;
  },

  async generateBasicResume(jobData) {
    const response = await api.post('/api/agents/basic-resume', jobData);
    return response.data;
  },

  async getAnalysisResults(analysisId) {
    const response = await api.get(`/api/analysis/results/${analysisId}`);
    return response.data;
  },

  async getExtendedAnalysisResults(analysisId) {
    const response = await api.get(`/api/analysis/extended-results/${analysisId}`);
    return response.data;
  },

  async downloadFile(analysisId, fileType) {
    const response = await api.get(`/api/analysis/download/${analysisId}/${fileType}`);
    return response.data;
  }
};

// Document service
export const documentService = {
  async generateDocuments(analysisId) {
    const response = await api.post('/api/documents/generate', { analysis_id: analysisId });
    return response.data;
  },

  async listUserDocuments() {
    const response = await api.get('/api/documents/list');
    return response.data;
  },

  async downloadDocument(documentId, fileType) {
    const response = await api.get(`/api/documents/download/${documentId}/${fileType}`, {
      responseType: 'blob'
    });
    return response.data;
  }
};

// Admin service
export const adminService = {
  async getDashboard(periodDays = 30) {
    const response = await api.get(`/api/admin/dashboard?period_days=${periodDays}`);
    return response.data;
  },

  async getUsers(page = 1, limit = 50) {
    const response = await api.get(`/api/admin/users?page=${page}&limit=${limit}`);
    return response.data;
  },

  async getEvents(eventType = null, periodDays = 7) {
    const params = new URLSearchParams({ period_days: periodDays });
    if (eventType) params.append('event_type', eventType);
    
    const response = await api.get(`/api/admin/analytics/events?${params}`);
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
  },

  async put(endpoint, data) {
    const response = await api.put(endpoint, data);
    return response.data;
  },

  async delete(endpoint) {
    const response = await api.delete(endpoint);
    return response.data;
  }
};

export default api;