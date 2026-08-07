import api from './api';

export const verdisService = {
  getHealth: () => api.get('/verdis/health').then(r => r.data),
  getNetwork: () => api.get('/verdis/network').then(r => r.data),
  getValidators: () => api.get('/verdis/validators').then(r => r.data),
  getSummary: () => api.get('/verdis/summary').then(r => r.data),
};

export default verdisService;
