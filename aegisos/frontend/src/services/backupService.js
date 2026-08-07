import api from './api';
export default {
  create: (description) => api.post('/backup/', { description }),
  restore: (data, restoreTypes) => api.post('/backup/restore', { data, restore_types: restoreTypes }),
  history: (limit) => api.get('/backup/history', { params: { limit } }),
  stats: () => api.get('/backup/stats'),
  last: () => api.get('/backup/last'),
};
