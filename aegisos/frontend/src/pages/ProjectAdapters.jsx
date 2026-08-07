import React, { useState, useEffect, useCallback } from 'react';
import api from '../services/api';

function ProjectAdapters() {
  const [adapters, setAdapters] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedAdapter, setSelectedAdapter] = useState(null);
  const [qualityGates, setQualityGates] = useState({});
  const [showRegister, setShowRegister] = useState(false);
  const [validation, setValidation] = useState(null);

  const fetchAdapters = useCallback(async () => {
    try {
      setLoading(true);
      const resp = await api.get('/project-adapters/');
      setAdapters(resp.data.adapters);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load adapters');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchAdapters(); }, [fetchAdapters]);

  const fetchQualityGates = async (typeId) => {
    try {
      const resp = await api.get(`/project-adapters/${typeId}/quality-gates`);
      setQualityGates(resp.data.commands);
    } catch (err) {
      setQualityGates({});
    }
  };

  const handleSelectAdapter = (adapter) => {
    setSelectedAdapter(adapter);
    setQualityGates({});
    fetchQualityGates(adapter.type_id);
  };

  const handleValidate = async (projectType, language) => {
    try {
      const resp = await api.post('/project-adapters/validate', {
        project_type: projectType,
        config: { language },
      });
      setValidation(resp.data);
    } catch (err) {
      setValidation({ valid: false, warnings: ['API error'] });
    }
  };

  if (loading) return <div className="loading">Loading project adapters...</div>;

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <h1 style={{ fontSize: '28px', fontWeight: 700, margin: 0 }}>Project Adapters</h1>
          <p style={{ color: '#888', marginTop: '4px' }}>
            {adapters.length} registered project type adapters — adapts EvolvixOS behavior per project domain
          </p>
        </div>
        <button
          onClick={() => setShowRegister(!showRegister)}
          style={{ padding: '8px 16px', background: '#4F46E5', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer' }}
        >
          {showRegister ? 'Cancel' : '+ Register Adapter'}
        </button>
      </div>

      {error && <div style={{ padding: '12px', background: '#FEF2F2', color: '#DC2626', borderRadius: '8px', marginBottom: '16px' }}>{error}</div>}

      {showRegister && <RegisterAdapterForm onCreated={() => { setShowRegister(false); fetchAdapters(); }} />}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
        {/* Adapter List */}
        <div>
          <h2 style={{ fontSize: '20px', marginBottom: '16px' }}>Available Adapters</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {adapters.map((adapter) => (
              <div
                key={adapter.type_id}
                onClick={() => handleSelectAdapter(adapter)}
                style={{
                  padding: '16px',
                  borderRadius: '10px',
                  border: selectedAdapter?.type_id === adapter.type_id ? '2px solid #4F46E5' : '1px solid #333',
                  cursor: 'pointer',
                  background: '#1A1A1E',
                  transition: 'border-color 0.2s',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <span style={{ fontSize: '24px' }}>{adapter.icon}</span>
                  <div>
                    <div style={{ fontWeight: 600, fontSize: '16px' }}>{adapter.display_name}</div>
                    <div style={{ fontSize: '13px', color: '#888' }}>{adapter.description}</div>
                  </div>
                </div>
                <div style={{ display: 'flex', gap: '8px', marginTop: '10px', flexWrap: 'wrap' }}>
                  {adapter.supported_languages.map((lang) => (
                    <span key={lang} style={{ padding: '2px 8px', fontSize: '11px', background: '#2A2A2E', borderRadius: '4px', color: '#A0A0A0' }}>{lang}</span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Adapter Detail */}
        <div>
          {selectedAdapter ? (
            <div>
              <h2 style={{ fontSize: '20px', marginBottom: '16px' }}>{selectedAdapter.icon} {selectedAdapter.display_name}</h2>
              <div style={{ background: '#1A1A1E', borderRadius: '10px', padding: '20px' }}>
                <DetailSection title="Default Language" value={selectedAdapter.default_language} />
                <DetailSection title="Supported Languages" value={selectedAdapter.supported_languages.join(', ')} />
                <DetailSection title="Task Types" items={selectedAdapter.task_types} />
                <DetailSection title="Quality Gates" items={selectedAdapter.quality_gates} />
                <DetailSection title="Security Checks" items={selectedAdapter.security_checks} />
                <DetailSection title="Monitoring Metrics" items={selectedAdapter.monitoring_metrics} />

                {Object.keys(qualityGates).length > 0 && (
                  <div style={{ marginTop: '16px' }}>
                    <h3 style={{ fontSize: '15px', marginBottom: '8px' }}>Quality Gate Commands</h3>
                    {Object.entries(qualityGates).map(([gate, cmd]) => (
                      <div key={gate} style={{ display: 'flex', gap: '8px', alignItems: 'center', padding: '6px 0', borderBottom: '1px solid #333' }}>
                        <code style={{ color: '#4F46E5', fontWeight: 600, minWidth: '120px' }}>{gate}</code>
                        <code style={{ color: '#A0A0A0', fontSize: '13px' }}>{cmd}</code>
                      </div>
                    ))}
                  </div>
                )}

                {selectedAdapter.file_structure && Object.keys(selectedAdapter.file_structure).length > 0 && (
                  <div style={{ marginTop: '16px' }}>
                    <h3 style={{ fontSize: '15px', marginBottom: '8px' }}>File Structure</h3>
                    {Object.entries(selectedAdapter.file_structure).map(([path, desc]) => (
                      <div key={path} style={{ display: 'flex', gap: '8px', padding: '4px 0' }}>
                        <code style={{ color: '#4F46E5', minWidth: '120px' }}>{path}</code>
                        <span style={{ color: '#888', fontSize: '13px' }}>{desc}</span>
                      </div>
                    ))}
                  </div>
                )}

                {validation && (
                  <div style={{ marginTop: '16px', padding: '12px', borderRadius: '8px', background: validation.valid ? '#1A3A1A' : '#3A1A1A', border: validation.valid ? '1px solid #22C55E' : '1px solid #EF4444' }}>
                    <div style={{ fontWeight: 600 }}>{validation.valid ? '✓ Valid' : '⚠ Validation Warnings'}</div>
                    {validation.warnings.map((w, i) => (
                      <div key={i} style={{ fontSize: '13px', color: '#FFA500', marginTop: '4px' }}>{w}</div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '300px', color: '#666' }}>
              Select an adapter to view details
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function DetailSection({ title, value, items }) {
  return (
    <div style={{ marginBottom: '12px' }}>
      <div style={{ fontSize: '13px', color: '#666', marginBottom: '4px' }}>{title}</div>
      {items ? (
        <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
          {items.map((item) => (
            <span key={item} style={{ padding: '3px 10px', fontSize: '12px', background: '#2A2A2E', borderRadius: '4px', color: '#CCC' }}>{item}</span>
          ))}
        </div>
      ) : (
        <div style={{ color: '#CCC', fontSize: '14px' }}>{value}</div>
      )}
    </div>
  );
}

function RegisterAdapterForm({ onCreated }) {
  const [form, setForm] = useState({
    type_id: '', display_name: '', description: '', default_language: 'python',
    supported_languages: ['python'], task_types: ['code_review'], quality_gates: ['lint', 'test', 'build'],
    security_checks: ['dependency_scan'],
  });
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await api.post('/project-adapters/', form);
      onCreated();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to register adapter');
    }
  };

  return (
    <form onSubmit={handleSubmit} style={{ background: '#1A1A1E', padding: '20px', borderRadius: '10px', marginBottom: '24px' }}>
      <h2 style={{ fontSize: '18px', marginBottom: '12px' }}>Register Custom Adapter</h2>
      {error && <div style={{ color: '#EF4444', marginBottom: '8px' }}>{error}</div>}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
        <input placeholder="Type ID (e.g. iot)" value={form.type_id} onChange={(e) => setForm({...form, type_id: e.target.value})} style={inputStyle} required />
        <input placeholder="Display Name" value={form.display_name} onChange={(e) => setForm({...form, display_name: e.target.value})} style={inputStyle} required />
        <input placeholder="Description" value={form.description} onChange={(e) => setForm({...form, description: e.target.value})} style={inputStyle} />
        <input placeholder="Default Language" value={form.default_language} onChange={(e) => setForm({...form, default_language: e.target.value})} style={inputStyle} />
      </div>
      <button type="submit" style={{ marginTop: '12px', padding: '8px 20px', background: '#4F46E5', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer' }}>Register</button>
    </form>
  );
}

const inputStyle = {
  padding: '8px 12px', background: '#0D0D0F', border: '1px solid #333', borderRadius: '6px', color: '#fff', fontSize: '14px',
};

export default ProjectAdapters;
