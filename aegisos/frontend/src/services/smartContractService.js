import api from './api';
export default {
  listTemplates: (cat) => api.get('/smart-contracts/templates', { params: { category: cat } }),
  getTemplate: (id) => api.get(`/smart-contracts/templates/${id}`),
  categories: () => api.get('/smart-contracts/categories'),
  scan: (data) => api.post('/smart-contracts/scan', data),
  getScan: (id) => api.get(`/smart-contracts/scan/${id}`),
  listScans: (limit) => api.get('/smart-contracts/scans', { params: { limit } }),
  register: (data) => api.post('/smart-contracts/register', data),
  verify: (id, data) => api.post(`/smart-contracts/contract/${id}/verify`, data),
  getContract: (id) => api.get(`/smart-contracts/contract/${id}`),
  getByAddress: (addr) => api.get(`/smart-contracts/contract/address/${addr}`),
  listContracts: (params) => api.get('/smart-contracts/contracts', { params }),
  deprecate: (id) => api.post(`/smart-contracts/contract/${id}/deprecate`),
  stats: () => api.get('/smart-contracts/stats'),
};
