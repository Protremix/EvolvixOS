import api from './api';
export default {
  listScenarios: (agent, tag) => api.get('/agent-enhancement/simulations', { params: { agent_name: agent, tag } }),
  getScenario: (id) => api.get(`/agent-enhancement/simulations/${id}`),
  createScenario: (data) => api.post('/agent-enhancement/simulations', data),
  runSimulation: (id) => api.post(`/agent-enhancement/simulations/${id}/run`),
  runAgentSim: (agent, type, data) => api.post('/agent-enhancement/simulations/run-agent', data, { params: { agent_name: agent, task_type: type } }),
  simHistory: (limit) => api.get('/agent-enhancement/simulations/history', { params: { limit } }),
  simStats: () => api.get('/agent-enhancement/simulations/stats'),
  verdisContext: () => api.get('/agent-enhancement/verdis-context'),
  verdisPrompt: () => api.get('/agent-enhancement/verdis-context/prompt'),
  taskTypes: () => api.get('/agent-enhancement/verdis-task-types'),
  toggleEnhancement: (enabled) => api.post(`/agent-enhancement/enhancement/${enabled}`),
  activities: (agent, limit) => api.get('/agent-enhancement/activities', { params: { agent_name: agent, limit } }),
  recordActivity: (data) => api.post('/agent-enhancement/activities', data),
  agentStats: () => api.get('/agent-enhancement/activities/stats'),
  overview: () => api.get('/agent-enhancement/overview'),
};
