import api from './api';
export default {
  dashboard: () => api.get('/deploy/dashboard'),
  scripts: (params) => api.get('/deploy/scripts', { params }),
  getScript: (id) => api.get(`/deploy/scripts/${id}`),
  getScriptByFilename: (fn) => api.get(`/deploy/scripts/filename/${fn}`),
  updateScriptStatus: (id, status) => api.patch(`/deploy/scripts/${id}/status`, { status }),
  generateAll: () => api.get('/deploy/scripts/generate-all'),
  dns: () => api.get('/deploy/dns'),
  ssl: () => api.get('/deploy/ssl'),
  steps: () => api.get('/deploy/steps'),
  updateStepStatus: (id, status) => api.patch(`/deploy/steps/${id}/status`, { status }),
  progress: () => api.get('/deploy/progress'),
};
