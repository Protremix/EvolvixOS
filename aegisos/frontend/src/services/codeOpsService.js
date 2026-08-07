import api from './api';

export const codeOpsService = {
  generateTests: (data) => api.post('/code-ops/generate-tests', data).then(r => r.data),
  diagnoseCI: (data) => api.post('/code-ops/diagnose-ci', data).then(r => r.data),
  getTestGeneratorInfo: () => api.get('/code-ops/agents/test-generator').then(r => r.data),
  getCIHealerInfo: () => api.get('/code-ops/agents/ci-healer').then(r => r.data),
};

export default codeOpsService;
