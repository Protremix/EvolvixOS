import api from './api';
export default {
  search: (q, entityTypes, limit) => api.get('/search/', { params: { q, entity_types: entityTypes?.join(','), limit } }),
  searchPost: (data) => api.post('/search/', data),
  types: () => api.get('/search/types'),
};
