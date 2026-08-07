import api from './api';
export default {
  compare: (runA, runB) => api.get(`/pipeline-comparison/${runA}/${runB}`),
};
