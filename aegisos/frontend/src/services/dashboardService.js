import api from './api';
export default {
  overview: () => api.get('/dashboard/overview'),
  performance: (limit) => api.get('/dashboard/performance', { params: { limit } }),
  clearPerformance: () => api.delete('/dashboard/performance'),
  exportPipelines: (format) => api.get('/export/pipelines', { params: { format }, responseType: format === 'csv' ? 'text' : 'json' }),
  exportAnalytics: (format) => api.get('/export/analytics', { params: { format }, responseType: format === 'csv' ? 'text' : 'json' }),
  exportKnowledge: (format) => api.get('/export/knowledge-base', { params: { format }, responseType: format === 'csv' ? 'text' : 'json' }),
  exportActivity: (format) => api.get('/export/activity-log', { params: { format }, responseType: format === 'csv' ? 'text' : 'json' }),
  exportAgentConfigs: (format) => api.get('/export/agent-configs', { params: { format }, responseType: format === 'csv' ? 'text' : 'json' }),
  exportSnapshot: () => api.get('/export/snapshot', { responseType: 'json' }),
};
