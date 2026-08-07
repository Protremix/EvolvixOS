import api from './api';
export default {
  register: (data) => api.post('/multi-project/projects', data),
  list: (type, status) => api.get('/multi-project/projects', { params: { type, status } }),
  get: (id) => api.get(`/multi-project/projects/${id}`),
  getByName: (name) => api.get(`/multi-project/projects/by-name/${name}`),
  update: (id, data) => api.put(`/multi-project/projects/${id}`, data),
  archive: (id) => api.post(`/multi-project/projects/${id}/archive`),
  pause: (id) => api.post(`/multi-project/projects/${id}/pause`),
  resume: (id) => api.post(`/multi-project/projects/${id}/resume`),
  agentConfig: (id, agent) => api.get(`/multi-project/projects/${id}/agent-config/${agent}`),
  learningContext: (id) => api.get(`/multi-project/projects/${id}/learning-context`),
  updateHealth: (id, status) => api.put(`/multi-project/projects/${id}/health`, null, { params: { status } }),
  stats: () => api.get('/multi-project/stats'),
};
