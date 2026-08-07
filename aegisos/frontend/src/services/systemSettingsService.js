import api from './api';
export default {
  list: (category) => api.get('/system-settings/', { params: category ? { category } : {} }),
  categories: () => api.get('/system-settings/categories'),
  get: (key) => api.get(`/system-settings/${key}`),
  set: (key, value) => api.put('/system-settings/', { key, value }),
  reset: (key) => api.delete(`/system-settings/${key}`),
  resetAll: () => api.post('/system-settings/reset-all'),
  export: () => api.get('/system-settings/export/all'),
  import: (settings) => api.post('/system-settings/import', settings),
};
