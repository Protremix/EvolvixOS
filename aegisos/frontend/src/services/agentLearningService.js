import api from './api';
export default {
  recordExecution: (data) => api.post('/agent-learning/executions', data),
  getExecutions: (agent, limit) => api.get('/agent-learning/executions', { params: { agent_name: agent, limit } }),
  analyze: () => api.post('/agent-learning/analyze'),
  insights: (agent, type, limit) => api.get('/agent-learning/insights', { params: { agent_name: agent, insight_type: type, limit } }),
  promptOpts: (agent) => api.get('/agent-learning/prompt-optimizations', { params: { agent_name: agent } }),
  performance: () => api.get('/agent-learning/performance'),
  agentPerformance: (name) => api.get(`/agent-learning/performance/${name}`),
  feedback: (name, task) => api.get(`/agent-learning/feedback/${name}`, { params: { task_type: task } }),
  summary: () => api.get('/agent-learning/summary'),
};
