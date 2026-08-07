import React, { useState } from 'react';
import { FileCode, Code, Play, CheckCircle, AlertTriangle, Copy } from 'lucide-react';
import specCompilerService from '../services/specCompilerService';

const SpecCompilerPage = () => {
  const [specInput, setSpecInput] = useState('');
  const [specFormat, setSpecFormat] = useState('openapi');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('models');

  const handleCompile = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await specCompilerService.compileString(specInput, specFormat);
      setResult(data);
    } catch (e) {
      setError(e.response ? e.response.data.detail : 'Compilation failed');
    }
    setLoading(false);
  };

  const codeFiles = result ? result.generated_code : {};
  const fileNames = Object.keys(codeFiles);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div>
        <h1 style={{ fontSize: '1.75rem', fontWeight: '800', color: '#f0fdf4' }}>Spec-Driven Compiler</h1>
        <p style={{ color: '#8e9b8e', marginTop: '0.25rem', fontSize: '0.875rem' }}>
          Compile OpenAPI/AsyncAPI specs into code blueprints
        </p>
      </div>

      {/* Format Selector */}
      <div style={{ display: 'flex', gap: '0.5rem' }}>
        <button
          onClick={() => setSpecFormat('openapi')}
          style={{
            padding: '0.375rem 1rem', borderRadius: '8px', fontSize: '0.8125rem', fontWeight: '600',
            cursor: 'pointer',
            backgroundColor: specFormat === 'openapi' ? 'rgba(0,255,136,0.12)' : '#0e140e',
            border: specFormat === 'openapi' ? '1px solid rgba(0,255,136,0.3)' : '1px solid #1f2e1f',
            color: specFormat === 'openapi' ? '#00ff88' : '#8e9b8e',
          }}
        >OpenAPI</button>
        <button
          onClick={() => setSpecFormat('asyncapi')}
          style={{
            padding: '0.375rem 1rem', borderRadius: '8px', fontSize: '0.8125rem', fontWeight: '600',
            cursor: 'pointer',
            backgroundColor: specFormat === 'asyncapi' ? 'rgba(168,85,247,0.12)' : '#0e140e',
            border: specFormat === 'asyncapi' ? '1px solid rgba(168,85,247,0.3)' : '1px solid #1f2e1f',
            color: specFormat === 'asyncapi' ? '#a855f7' : '#8e9b8e',
          }}
        >AsyncAPI</button>
      </div>

      {/* Spec Input */}
      <div className="card">
        <label style={{ fontSize: '0.8125rem', color: '#8e9b8e', marginBottom: '0.375rem', display: 'block' }}>
          {specFormat === 'openapi' ? 'OpenAPI' : 'AsyncAPI'} JSON Spec
        </label>
        <textarea
          value={specInput}
          onChange={(e) => setSpecInput(e.target.value)}
          placeholder={'Paste your ' + specFormat + ' JSON spec here...'}
          style={{
            width: '100%', minHeight: '220px', padding: '0.75rem',
            backgroundColor: '#0e140e', border: '1px solid #1f2e1f',
            borderRadius: '8px', color: '#f0fdf4', fontFamily: 'monospace',
            fontSize: '0.8125rem', resize: 'vertical', outline: 'none',
          }}
        />
        <button
          onClick={handleCompile}
          disabled={loading || !specInput.trim()}
          style={{
            marginTop: '0.75rem', padding: '0.5rem 1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem',
            backgroundColor: loading || !specInput.trim() ? '#1f2e1f' : 'rgba(0,255,136,0.12)',
            border: loading || !specInput.trim() ? '1px solid #1f2e1f' : '1px solid rgba(0,255,136,0.3)',
            borderRadius: '8px', color: loading || !specInput.trim() ? '#526352' : '#00ff88',
            fontSize: '0.875rem', fontWeight: '600', cursor: loading || !specInput.trim() ? 'not-allowed' : 'pointer',
          }}
        >
          <Play size={18} /> {loading ? 'Compiling...' : 'Compile Spec'}
        </button>
      </div>

      {error && (
        <div className="card" style={{ border: '1px solid rgba(239,68,68,0.3)' }}>
          <p style={{ color: '#ef4444', fontSize: '0.875rem' }}>Error: {error}</p>
        </div>
      )}

      {/* Results */}
      {result && (
        <>
          {/* Stats */}
          <div className="grid-4">
            <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
              <span style={{ fontSize: '0.8125rem', color: '#8e9b8e' }}>Models</span>
              <span style={{ fontSize: '1.5rem', fontWeight: '800', color: '#f0fdf4' }}>{result.stats.total_models}</span>
            </div>
            <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
              <span style={{ fontSize: '0.8125rem', color: '#8e9b8e' }}>Endpoints</span>
              <span style={{ fontSize: '1.5rem', fontWeight: '800', color: '#f0fdf4' }}>{result.stats.total_endpoints}</span>
            </div>
            <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
              <span style={{ fontSize: '0.8125rem', color: '#8e9b8e' }}>Fields</span>
              <span style={{ fontSize: '1.5rem', fontWeight: '800', color: '#f0fdf4' }}>{result.stats.total_fields}</span>
            </div>
            <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
              <span style={{ fontSize: '0.8125rem', color: '#8e9b8e' }}>Generated Files</span>
              <span style={{ fontSize: '1.5rem', fontWeight: '800', color: '#00ff88' }}>{result.stats.generated_files}</span>
            </div>
          </div>

          {/* Models */}
          {result.models && result.models.length > 0 && (
            <div className="card">
              <h2 style={{ fontSize: '1.1rem', fontWeight: '700', color: '#f0fdf4', marginBottom: '1rem' }}>Models ({result.models.length})</h2>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {result.models.map((model, i) => (
                  <div key={i} style={{ padding: '0.5rem 0.75rem', backgroundColor: '#0e140e', border: '1px solid #1f2e1f', borderRadius: '8px' }}>
                    <div style={{ fontSize: '0.875rem', fontWeight: '600', color: '#00ff88', fontFamily: 'monospace' }}>{model.name}</div>
                    {model.description && <div style={{ fontSize: '0.75rem', color: '#8e9b8e', marginTop: '0.25rem' }}>{model.description}</div>}
                    <div style={{ marginTop: '0.375rem', display: 'flex', flexWrap: 'wrap', gap: '0.25rem' }}>
                      {model.fields.map((f, j) => (
                        <span key={j} style={{ fontSize: '0.6875rem', padding: '0.125rem 0.5rem', borderRadius: '4px', fontFamily: 'monospace', backgroundColor: 'rgba(59,130,246,0.1)', color: '#3b82f6' }}>
                          {f.name}: {f.type}{f.required ? '' : '?'}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Endpoints */}
          {result.endpoints && result.endpoints.length > 0 && (
            <div className="card">
              <h2 style={{ fontSize: '1.1rem', fontWeight: '700', color: '#f0fdf4', marginBottom: '1rem' }}>Endpoints ({result.endpoints.length})</h2>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.375rem' }}>
                {result.endpoints.map((ep, i) => (
                  <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.375rem 0.75rem', backgroundColor: '#0e140e', border: '1px solid #1f2e1f', borderRadius: '8px' }}>
                    <span style={{ fontSize: '0.6875rem', fontWeight: '700', padding: '0.125rem 0.5rem', borderRadius: '4px', fontFamily: 'monospace',
                      backgroundColor: ep.method === 'GET' ? 'rgba(59,130,246,0.15)' : ep.method === 'POST' ? 'rgba(0,255,136,0.15)' : ep.method === 'DELETE' ? 'rgba(239,68,68,0.15)' : 'rgba(245,158,11,0.15)',
                      color: ep.method === 'GET' ? '#3b82f6' : ep.method === 'POST' ? '#00ff88' : ep.method === 'DELETE' ? '#ef4444' : '#f59e0b',
                    }}>{ep.method}</span>
                    <span style={{ fontSize: '0.8125rem', color: '#f0fdf4', fontFamily: 'monospace', flex: 1 }}>{ep.path}</span>
                    {ep.response_model && <span style={{ fontSize: '0.6875rem', color: '#a855f7' }}>{'-> ' + ep.response_model}</span>}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Generated Code */}
          {fileNames.length > 0 && (
            <div className="card">
              <h2 style={{ fontSize: '1.1rem', fontWeight: '700', color: '#f0fdf4', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Code size={20} color="#00ff88" /> Generated Code
              </h2>
              <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.75rem' }}>
                {fileNames.map(fname => (
                  <button
                    key={fname}
                    onClick={() => setActiveTab(fname)}
                    style={{
                      padding: '0.25rem 0.75rem', borderRadius: '6px', fontSize: '0.75rem', fontWeight: '600',
                      cursor: 'pointer', fontFamily: 'monospace',
                      backgroundColor: activeTab === fname ? 'rgba(0,255,136,0.12)' : '#0e140e',
                      border: activeTab === fname ? '1px solid rgba(0,255,136,0.3)' : '1px solid #1f2e1f',
                      color: activeTab === fname ? '#00ff88' : '#8e9b8e',
                    }}
                  >{fname}</button>
                ))}
              </div>
              <pre style={{
                backgroundColor: '#0e140e', border: '1px solid #1f2e1f', borderRadius: '8px',
                padding: '1rem', overflow: 'auto', fontSize: '0.75rem', color: '#f0fdf4',
                fontFamily: 'monospace', maxHeight: '350px',
              }}>
                {codeFiles[activeTab] || codeNames[0] || ''}
              </pre>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default SpecCompilerPage;
