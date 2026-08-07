import api from './api';
export default {
  health: () => api.get('/monitor/health'),
  services: () => api.get('/monitor/services'),
  system: () => api.get('/monitor/system'),
  metrics: (name, limit) => api.get(`/monitor/metrics/${name}?limit=${limit || 100}`),
  check: () => api.post('/monitor/check'),
  start: (interval) => api.post(`/monitor/monitoring/start?interval=${interval || 30}`),
  stop: () => api.post('/monitor/monitoring/stop'),
};
