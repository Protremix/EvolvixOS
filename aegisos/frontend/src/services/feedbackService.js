import api from './api';
export default {
  submit: (data) => api.post('/feedback', data),
  list: (category, status, limit) => api.get('/feedback', { params: { category, status, limit } }),
  get: (id) => api.get(`/feedback/${id}`),
  respond: (id, response, status) => api.post(`/feedback/${id}/respond`, { response, status }),
  acknowledge: (id) => api.post(`/feedback/${id}/acknowledge`),
  dismiss: (id) => api.post(`/feedback/${id}/dismiss`),
  stats: () => api.get('/feedback/stats'),
};
