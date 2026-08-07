import api from './api';
export default {
  circuitBreakers: () => api.get('/security/circuit-breakers'),
  resetCircuitBreaker: (name) => api.post(`/security/circuit-breakers/${name}/reset`),
  authRateLimitStats: () => api.get('/security/auth-rate-limit/stats'),
  jwtConfig: () => api.get('/security/jwt-config'),
  secretManagerConfig: () => api.get('/security/secret-manager/config'),
  paginationDemo: () => api.get('/security/pagination/demo'),
  summary: () => api.get('/security/summary'),
};
