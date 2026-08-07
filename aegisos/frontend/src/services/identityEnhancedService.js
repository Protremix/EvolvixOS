import api from './api';
export default {
  getSchema: (type) => api.get(`/identity-enhanced/schema/${type}`),
  listSchemas: () => api.get('/identity-enhanced/schemas'),
  createSchema: (data) => api.post('/identity-enhanced/schemas/custom', data),
  validate: (data) => api.post('/identity-enhanced/validate', data),
  resolveDID: (did) => api.get(`/identity-enhanced/resolve/${did}`),
  createPresentation: (data) => api.post('/identity-enhanced/presentation/create', data),
  getPresentation: (id) => api.get(`/identity-enhanced/presentation/${id}`),
  verifyPresentation: (id) => api.get(`/identity-enhanced/presentation/${id}/verify`),
  listPresentations: (holder, limit) => api.get('/identity-enhanced/presentations', { params: { holder_did: holder, limit } }),
  sdkInfo: () => api.get('/identity-enhanced/sdk-info'),
};
