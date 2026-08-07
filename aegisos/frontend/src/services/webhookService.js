import api from './api';
export default {
  events: () => api.get('/webhooks/events'),
  list: (activeOnly) => api.get('/webhooks/', { params: activeOnly ? { active_only: true } : {} }),
  create: (data) => api.post('/webhooks/', data),
  get: (id) => api.get(`/webhooks/${id}`),
  update: (id, updates) => api.patch(`/webhooks/${id}`, updates),
  delete: (id) => api.delete(`/webhooks/${id}`),
  test: (id) => api.post(`/webhooks/${id}/test`),
  activate: (id) => api.post(`/webhooks/${id}/activate`),
  deactivate: (id) => api.post(`/webhooks/${id}/deactivate`),
  deliveries: (id, limit) => api.get(`/webhooks/${id}/deliveries`, { params: { limit } }),
  recentDeliveries: (limit) => api.get('/webhooks/deliveries/recent', { params: { limit } }),
  stats: () => api.get('/webhooks/stats'),
};
