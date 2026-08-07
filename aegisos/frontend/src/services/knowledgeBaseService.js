import api from './api';

export default {
  list: (params) => api.get('/knowledge-base/', { params }),
  create: (entry) => api.post('/knowledge-base/', entry),
  get: (id) => api.get(`/knowledge-base/${id}`),
  update: (id, updates) => api.patch(`/knowledge-base/${id}`, updates),
  delete: (id) => api.delete(`/knowledge-base/${id}`),
  search: (q) => api.get('/knowledge-base/search', { params: { q } }),
  stats: () => api.get('/knowledge-base/stats'),
  patterns: (type) => api.get('/knowledge-base/patterns/list', { params: type ? { pattern_type: type } : {} }),
  deletePattern: (id) => api.delete(`/knowledge-base/patterns/${id}`),
  extractPatterns: () => api.post('/knowledge-base/patterns/extract'),
  extractLessons: (pipelineId) => api.post(`/knowledge-base/lessons/${pipelineId}`),
};
