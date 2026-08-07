import api from './api';

export const depGraphService = {
  build: (projectPath, ignoreDirs = []) => api.post('/dep-graph/build', { project_path: projectPath, ignore_dirs: ignoreDirs }).then(r => r.data),
  getStats: (projectPath) => api.get('/dep-graph/stats', { params: { project_path: projectPath } }).then(r => r.data),
  getCycles: (projectPath) => api.get('/dep-graph/cycles', { params: { project_path: projectPath } }).then(r => r.data),
  getDependencies: (projectPath) => api.get('/dep-graph/dependencies', { params: { project_path: projectPath } }).then(r => r.data),
  getImpact: (filePath) => api.post('/dep-graph/impact', { file_path: filePath }).then(r => r.data),
  clearCache: (projectPath) => api.delete('/dep-graph/cache', { params: { project_path: projectPath } }).then(r => r.data),
};

export default depGraphService;
