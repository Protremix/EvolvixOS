import api from './api';
export default {
  createDID: (data) => api.post('/identity/did/create', data),
  getDID: (did) => api.get(`/identity/did/${did}`),
  listDIDs: (limit, offset) => api.get('/identity/did/list', { params: { limit, offset } }),
  getProfile: (did) => api.get(`/identity/profile/${did}`),
  updateProfile: (did, data) => api.patch(`/identity/profile/${did}`, data),
  verifyIdentity: (did) => api.post(`/identity/profile/${did}/verify`),
  issueCredential: (data) => api.post('/identity/credential/issue', data),
  getCredential: (id) => api.get(`/identity/credential/${id}`),
  verifyCredential: (id) => api.get(`/identity/credential/${id}/verify`),
  revokeCredential: (id) => api.post(`/identity/credential/${id}/revoke`),
  listCredentials: (did, limit) => api.get('/identity/credentials', { params: { did, limit } }),
  updateReputation: (did, delta) => api.post(`/identity/reputation/${did}`, null, { params: { delta } }),
  stats: () => api.get('/identity/stats'),
};
