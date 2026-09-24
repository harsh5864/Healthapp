import apiClient from './apiClient';

export const authApi = {
  register: (data) => apiClient.post('/auth/register', data),
  login: (data) => apiClient.post('/auth/login', data),
  profile: () => apiClient.get('/users/profile'),
  updateProfile: (data) => apiClient.put('/users/profile', data),
};
export const dashboardApi = { summary: () => apiClient.get('/dashboard/summary') };
export const foodApi = {
  analyze: (file, scanType = 'PRODUCE') => {
    const form = new FormData();
    form.append('image', file);
    return apiClient.post(`/food/analyze?scanType=${encodeURIComponent(scanType)}`, form);
  },
  history: () => apiClient.get('/food/history'),
  remove: (id) => apiClient.delete(`/food/${id}`)
};
export const chatApi = { conversations: () => apiClient.get('/chat/conversations'), create: (title) => apiClient.post('/chat/conversations', { title }), messages: (id) => apiClient.get(`/chat/conversations/${id}/messages`), send: (id, message) => apiClient.post(`/chat/conversations/${id}/messages`, { message }), remove: (id) => apiClient.delete(`/chat/conversations/${id}`) };
export const wellnessApi = { summary: () => apiClient.get('/wellness/summary'), history: () => apiClient.get('/wellness/history'), checkIn: (data) => apiClient.post('/wellness/check-in', data), trends: () => apiClient.get('/wellness/trends') };
export const nutrientApi = {
  log: (data) => apiClient.post('/nutrients/log', data),
  get3DaySummary: () => apiClient.get('/nutrients/3-day-summary'),
  remove: (id) => apiClient.delete(`/nutrients/${id}`),
};
