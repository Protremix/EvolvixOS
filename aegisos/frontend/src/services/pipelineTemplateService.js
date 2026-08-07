import api from './api';

export default {
  list: (category) => api.get('/pipeline-templates/', { params: category ? { category } : {} }),
  get: (id) => api.get(`/pipeline-templates/${id}`),
  categories: () => api.get('/pipeline-templates/categories'),
  apply: (id, title, description) => api.post(`/pipeline-templates/${id}/apply`, null, { params: { title, description } }),
  createPipeline: (id, title, description) => api.post(`/pipeline-templates/${id}/create-pipeline`, null, { params: { title, description } }),
  create: (template) => api.post('/pipeline-templates/', template),
  delete: (id) => api.delete(`/pipeline-templates/${id}`),
  // Notifications
  getNotifications: (unreadOnly) => api.get('/notifications/', { params: { unread_only: unreadOnly } }),
  getUnreadCount: () => api.get('/notifications/unread-count'),
  markRead: (id) => api.post(`/notifications/${id}/read`),
  markAllRead: () => api.post('/notifications/read-all'),
  clear: () => api.delete('/notifications/'),
};
