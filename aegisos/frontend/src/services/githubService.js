import api from './api';

export const githubService = {
  getRepo: (owner, repo) => api.get(`/github/repos/${owner}/${repo}`).then(r => r.data),
  listIssues: (owner, repo, state = 'open') => api.get(`/github/repos/${owner}/${repo}/issues`, { params: { state } }).then(r => r.data),
  listPRs: (owner, repo, state = 'open') => api.get(`/github/repos/${owner}/${repo}/pulls`, { params: { state } }).then(r => r.data),
  listCommits: (owner, repo, perPage = 10) => api.get(`/github/repos/${owner}/${repo}/commits`, { params: { per_page: perPage } }).then(r => r.data),
  listWorkflowRuns: (owner, repo, perPage = 10) => api.get(`/github/repos/${owner}/${repo}/actions/runs`, { params: { per_page: perPage } }).then(r => r.data),
};

export default githubService;
