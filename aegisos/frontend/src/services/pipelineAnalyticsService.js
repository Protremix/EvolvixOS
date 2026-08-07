import api from './api';

export default {
  overview: () => api.get('/pipeline-analytics/overview'),
  summary: () => api.get('/pipeline-analytics/summary'),
  stages: () => api.get('/pipeline-analytics/stages'),
  agents: () => api.get('/pipeline-analytics/agents'),
  throughput: (period, days) => api.get('/pipeline-analytics/throughput', { params: { period, days } }),
  bottlenecks: (threshold) => api.get('/pipeline-analytics/bottlenecks', { params: { threshold } }),
  trends: (days) => api.get('/pipeline-analytics/trends', { params: { days } }),
  // Scheduler
  listSchedules: (enabledOnly) => api.get('/pipeline-scheduler/', { params: enabledOnly ? { enabled_only: true } : {} }),
  createSchedule: (sched) => api.post('/pipeline-scheduler/', sched),
  getSchedule: (id) => api.get(`/pipeline-scheduler/${id}`),
  updateSchedule: (id, updates) => api.patch(`/pipeline-scheduler/${id}`, updates),
  deleteSchedule: (id) => api.delete(`/pipeline-scheduler/${id}`),
  enableSchedule: (id) => api.post(`/pipeline-scheduler/${id}/enable`),
  disableSchedule: (id) => api.post(`/pipeline-scheduler/${id}/disable`),
  checkTrigger: () => api.post('/pipeline-scheduler/check'),
  upcoming: (limit) => api.get('/pipeline-scheduler/upcoming/list', { params: { limit } }),
};
