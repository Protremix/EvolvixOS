import api from './api';
export default {
  dashboard: () => api.get('/evolvixos-infra/dashboard'),
  components: () => api.get('/evolvixos-infra/components'),
  updateComponent: (id, status) => api.patch(`/evolvixos-infra/components/${id}/status`, { status }),
  dns: () => api.get('/evolvixos-infra/dns'),
  steps: () => api.get('/evolvixos-infra/steps'),
  updateStep: (id, status) => api.patch(`/evolvixos-infra/steps/${id}/status`, { status }),
  scripts: () => api.get('/evolvixos-infra/scripts'),
  setIP: (ip) => api.post('/evolvixos-infra/set-ip', { ip }),
  progress: () => api.get('/evolvixos-infra/progress'),
};
