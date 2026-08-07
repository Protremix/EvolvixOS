import api from './api';
export default {
  register: () => api.post('/verdis-project/register'),
  healthCheck: () => api.post('/verdis-project/health-check'),
  overview: () => api.get('/verdis-project/overview'),
  health: () => api.get('/verdis-project/health'),
  healthHistory: (limit) => api.get('/verdis-project/health/history', { params: { limit } }),
  components: () => api.get('/verdis-project/components'),
  updateComponent: (data) => api.put('/verdis-project/components', data),
  alerts: (resolved) => api.get('/verdis-project/alerts', { params: { resolved } }),
  resolveAlert: (alertId) => api.post('/verdis-project/alerts/resolve', { alert_id: alertId }),
  agentContext: () => api.get('/verdis-project/agent-context'),
  healthSummary: () => api.get('/verdis-project/health-summary'),
  pipelineTemplate: () => api.get('/verdis-project/pipeline-template'),
  stats: () => api.get('/verdis-project/stats'),
  toggleMonitoring: (enabled) => api.post(`/verdis-project/monitoring/${enabled}`),
};
