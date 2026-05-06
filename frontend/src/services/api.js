import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Handle auth errors
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  login: (username, password) =>
    api.post('/api/v1/auth/login', { username, password }),

  register: (userData) =>
    api.post('/api/v1/auth/register', userData),

  getProfile: () =>
    api.get('/api/v1/auth/me'),

  refreshToken: (refreshToken) =>
    api.post('/api/v1/auth/refresh', { refresh_token: refreshToken }),
};

export const dataAPI = {
  generatePatients: (params) =>
    api.post('/api/v1/generate/patients', params),

  generateVitals: (inputFile) =>
    api.post('/api/v1/generate/vitals', { input_file: inputFile }),

  generateBatch: (params) =>
    api.post('/api/v1/generate/batch', params),

  applyPrivacy: (params) =>
    api.post('/api/v1/privacy/apply', params),

  computeStatistics: (params) =>
    api.post('/api/v1/privacy/statistics', params),

  simulateProgression: (params) =>
    api.post('/api/v1/simulate/progression', params),
};

export const utilsAPI = {
  healthCheck: () =>
    api.get('/health'),

  apiDocs: () =>
    api.get('/api/v1/docs'),
};

export default api;
