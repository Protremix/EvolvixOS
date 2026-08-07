import api from './api';
export default {
  listAgents: () => api.get('/agent-config/agents'),
  listModels: () => api.get('/agent-config/models'),
  effectiveConfig: (agent, projectId) => api.get(`/agent-config/effective/${agent}`, { params: projectId ? { project_id: projectId } : {} }),
  projectConfig: (projectId) => api.get(`/agent-config/project/${projectId}`),
  setProjectConfig: (projectId, agent, config) => api.put(`/agent-config/project/${projectId}/${agent}`, config),
  deleteProjectConfig: (projectId, agent) => api.delete(`/agent-config/project/${projectId}/${agent}`),
  globalOverride: (agent) => api.get(`/agent-config/global/${agent}`),
  setGlobalOverride: (agent, config) => api.put(`/agent-config/global/${agent}`, config),
  deleteGlobalOverride: (agent) => api.delete(`/agent-config/global/${agent}`),
  enabledAgents: (projectId) => api.get('/agent-config/enabled/list', { params: projectId ? { project_id: projectId } : {} }),
};
