import axios from 'axios';

/**
 * Single HTTP boundary for the React application. Future auth interceptors and
 * feature services attach here instead of scattering API URLs through pages.
 */
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 10_000,
  headers: { Accept: 'application/json' },
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('health_companion_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

apiClient.interceptors.response.use((response) => response, (error) => {
  if (error.response?.status === 401) {
    localStorage.removeItem('health_companion_token');
    localStorage.removeItem('health_companion_user');
  }
  return Promise.reject(error);
});

export default apiClient;
