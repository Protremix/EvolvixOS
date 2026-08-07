import api from './api';

export const aiService = {
  // Agents
  getAgents: () => api.get('/ai/agents').then(r => Array.isArray(r.data) ? r.data : r.data.items || []),

  // Tasks
  createTask: (data) => api.post('/ai/tasks', data).then(r => r.data),
  getTaskResult: (taskId) => api.get(`/ai/dispatch/${taskId}/result`).then(r => r.data),

  // Pipelines
  createPipeline: (data) => api.post('/ai/pipelines', data).then(r => r.data),

  // Dispatch
  dispatchTask: (data) => api.post('/ai/dispatch', data).then(r => r.data),
  dispatchBatch: (tasks) => api.post('/ai/dispatch/batch', tasks).then(r => r.data),

  // Executor
  getExecutorStatus: () => api.get('/ai/executor/status').then(r => r.data),

  // Health
  getHealth: () => api.get('/ai/health').then(r => r.data),
};

export default aiService;
