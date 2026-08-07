import api from './api';

export const specCompilerService = {
  compile: (spec, format = 'openapi') => api.post('/spec-compiler/compile', { spec, spec_format: format }).then(r => r.data),
  compileString: (specJson, format = 'openapi') => api.post('/spec-compiler/compile-string', { spec_json: specJson, spec_format: format }).then(r => r.data),
  validate: (spec, format = 'openapi') => api.post('/spec-compiler/validate', { spec, spec_format: format }).then(r => r.data),
  getInfo: () => api.get('/spec-compiler/info').then(r => r.data),
};

export default specCompilerService;
