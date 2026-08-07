import api from './api';
export default {
  create: (data) => api.post('/deployment/create', data),
  get: (id) => api.get(`/deployment/${id}`),
  update: (id, data) => api.patch(`/deployment/${id}`, data),
  addLog: (id, level, message) => api.post(`/deployment/${id}/log`, null, { params: { level, message } }),
  rollback: (id) => api.post(`/deployment/${id}/rollback`),
  list: (params) => api.get('/deployment/list/deployments', { params }),
  environments: () => api.get('/deployment/environments'),
  getEnvironment: (target) => api.get(`/deployment/environments/${target}`),
  updateEnvironment: (target, data) => api.patch(`/deployment/environments/${target}`, data),
  stats: () => api.get('/deployment/stats'),
  workflows: () => api.get('/deployment/workflows'),
  components: () => api.get('/deployment/components'),
  targets: () => api.get('/deployment/targets'),
};
