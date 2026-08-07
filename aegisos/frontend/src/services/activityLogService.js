import api from './api';
export default {
  list: (params) => api.get('/activity-log/', { params }),
  search: (q) => api.get('/activity-log/search', { params: { q } }),
  stats: () => api.get('/activity-log/stats'),
  recentErrors: (limit) => api.get('/activity-log/errors/recent', { params: { limit } }),
  create: (entry) => api.post('/activity-log/', entry),
  cleanup: (maxAgeDays) => api.post('/activity-log/cleanup', null, { params: { max_age_days: maxAgeDays } }),
};
