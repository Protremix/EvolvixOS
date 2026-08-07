import api from './api';

export const astDiffService = {
  compare: (oldCode, newCode, language = 'python') => api.post('/ast-diff/compare', { old_code: oldCode, new_code: newCode, language }).then(r => r.data),
  compareFiles: (oldFile, newFile, language = 'python') => api.post('/ast-diff/compare-files', { old_file: oldFile, new_file: newFile, language }).then(r => r.data),
  getInfo: () => api.get('/ast-diff/info').then(r => r.data),
};

export default astDiffService;
