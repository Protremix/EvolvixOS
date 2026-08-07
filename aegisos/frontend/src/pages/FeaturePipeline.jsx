import React, { useState, useEffect, useCallback, useRef } from 'react';
import api from '../services/api';

function FeaturePipeline() {
  const [pipelines, setPipelines] = useState([]);
  const [stages, setStages] = useState([]);
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedPipeline, setSelectedPipeline] = useState(null);
  const [showCreate, setShowCreate] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);
  const wsRef = useRef(null);

  const fetchPipelines = useCallback(async () => {
    try {
      const resp = await api.get('/feature-pipeline/');
      setPipelines(resp.data);
    } catch (err) { console.error('Failed to load pipelines', err); }
    finally { setLoading(false); }
  }, []);

  const fetchStages = useCallback(async () => {
    try {
      const resp = await api.get('/feature-pipeline/stages/info');
      setStages(resp.data);
    } catch (err) { console.error('Failed to load stages', err); }
  }, []);

  useEffect(() => {
    fetchPipelines();
    fetchStages();

    // WebSocket connection for live events
    const wsUrl = `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}/api/v1/feature-pipeline/ws`;
    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;
      ws.onopen = () => setWsConnected(true);
      ws.onclose = () => { setWsConnected(false); setTimeout(() => ws.close(), 100); };
      ws.onmessage = (e) => {
        try {
          const evt = JSON.parse(e.data);
          setEvents(prev => [...prev.slice(-50), evt]);
          // Refresh pipeline data if event matches selected pipeline
          if (selectedPipeline && evt.pipeline_id === selectedPipeline.id) {
            fetchPipelines();
          }
        } catch {}
      };
      return () => ws.close();
    } catch { /* offline mode */ }
  }, []);

  const handleCreate = async (feature) => {
    try {
      const resp = await api.post('/feature-pipeline/', feature);
      setShowCreate(false);
      fetchPipelines();
      setSelectedPipeline(resp.data);
    } catch (err) { console.error('Failed to create pipeline', err); }
  };

  const handleExecute = async (pipelineId) => {
    try {
      await api.post(`/feature-pipeline/${pipelineId}/execute`);
      fetchPipelines();
    } catch (err) { console.error('Failed to execute pipeline', err); }
  };

  const handleCancel = async (pipelineId) => {
    try {
      await api.post(`/feature-pipeline/${pipelineId}/cancel`);
      fetchPipelines();
    } catch (err) { console.error('Failed to cancel', err); }
  };

  if (loading) return <div style={{ padding: '24px', color: '#888' }}>Loading pipelines...</div>;

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <h1 style={{ fontSize: '28px', fontWeight: 700, margin: 0 }}>Feature Delivery Pipeline</h1>
          <p style={{ color: '#888', marginTop: '4px' }}>
            10-stage autonomous pipeline: PRD → Architecture → Implementation → QA → Security → Release
          </p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{
            padding: '4px 10px', fontSize: '11px', borderRadius: '4px',
            background: wsConnected ? '#0D3D1A' : '#3D1A0D', color: wsConnected ? '#22C55E' : '#EF4444',
          }}>
            {wsConnected ? '● Live' : '● Offline'}
          </span>
          <button onClick={() => setShowCreate(!showCreate)} style={btnPrimary}>
            {showCreate ? 'Cancel' : '+ New Pipeline'}
          </button>
        </div>
      </div>

      {/* Pipeline Stages Overview */}
      <div style={{ background: '#1A1A1E', borderRadius: '10px', padding: '16px', marginBottom: '24px' }}>
        <h2 style={{ fontSize: '16px', marginBottom: '12px' }}>Pipeline Stages ({stages.length})</h2>
        <div style={{ display: 'flex', gap: '4px', overflowX: 'auto' }}>
          {stages.map((stage, i) => (
            <div key={stage.stage} style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <div style={{ padding: '6px 12px', borderRadius: '6px', background: '#0D0D0F', border: '1px solid #333', whiteSpace: 'nowrap', fontSize: '12px' }}>
                <div style={{ color: '#4F46E5', fontWeight: 600 }}>{i + 1}. {stage.name}</div>
                <div style={{ color: '#666', fontSize: '11px' }}>{stage.agent}</div>
              </div>
              {i < stages.length - 1 && <span style={{ color: '#333' }}>→</span>}
            </div>
          ))}
        </div>
      </div>

      {showCreate && <CreatePipelineForm onCreate={handleCreate} />}

      {/* Live Event Feed */}
      {events.length > 0 && (
        <div style={{ background: '#1A1A1E', borderRadius: '10px', padding: '12px', marginBottom: '24px', maxHeight: '200px', overflowY: 'auto' }}>
          <h3 style={{ fontSize: '14px', marginBottom: '8px', color: '#4F46E5' }}>Live Events ({events.length})</h3>
          {events.slice(-10).reverse().map((evt, i) => (
            <div key={i} style={{ display: 'flex', gap: '8px', padding: '4px 0', fontSize: '12px', borderBottom: '1px solid #222' }}>
              <span style={{ color: '#666', minWidth: '80px' }}>{new Date(evt.timestamp).toLocaleTimeString()}</span>
              <span style={{ color: evtColor(evt.event_type), minWidth: '180px' }}>{evt.event_type}</span>
              <span style={{ color: '#999' }}>{evt.message}</span>
            </div>
          ))}
        </div>
      )}

      {/* Pipeline List + Detail View */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
        <div>
          <h2 style={{ fontSize: '20px', marginBottom: '16px' }}>Pipeline Runs ({pipelines.length})</h2>
          {pipelines.length === 0 ? (
            <div style={{ padding: '32px', textAlign: 'center', color: '#666', background: '#1A1A1E', borderRadius: '10px' }}>
              No pipeline runs yet. Click "New Pipeline" to start one.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {pipelines.map((p) => (
                <div key={p.id} onClick={() => setSelectedPipeline(p)} style={{
                  padding: '16px', borderRadius: '10px', cursor: 'pointer', background: '#1A1A1E',
                  border: selectedPipeline?.id === p.id ? '2px solid #4F46E5' : '1px solid #333',
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ fontWeight: 600 }}>{p.feature.title}</span>
                    <span style={{ fontSize: '11px', padding: '2px 8px', borderRadius: '4px', ...statusBadge(p.status) }}>{p.status}</span>
                  </div>
                  <div style={{ fontSize: '13px', color: '#888', marginTop: '4px' }}>{p.feature.description}</div>
                  {p.status === 'pending' && (
                    <button onClick={(e) => { e.stopPropagation(); handleExecute(p.id); }} style={{ ...btnSmall, marginTop: '8px' }}>▶ Execute</button>
                  )}
                  {p.status === 'running' && (
                    <button onClick={(e) => { e.stopPropagation(); handleCancel(p.id); }} style={{ ...btnSmall, marginTop: '8px', background: '#5C1A1A' }}>■ Cancel</button>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Detail View */}
        <div>
          {selectedPipeline ? (
            <div>
              <h2 style={{ fontSize: '20px', marginBottom: '16px' }}>{selectedPipeline.feature.title}</h2>
              <div style={{ background: '#1A1A1E', borderRadius: '10px', padding: '20px' }}>
                <div style={{ marginBottom: '16px' }}>
                  <div style={{ fontSize: '13px', color: '#666', marginBottom: '4px' }}>Description</div>
                  <div style={{ color: '#CCC' }}>{selectedPipeline.feature.description}</div>
                </div>
                {selectedPipeline.feature.constraints?.length > 0 && (
                  <div style={{ marginBottom: '16px' }}>
                    <div style={{ fontSize: '13px', color: '#666', marginBottom: '4px' }}>Constraints</div>
                    {selectedPipeline.feature.constraints.map((c, i) => (
                      <div key={i} style={{ fontSize: '13px', color: '#FFA500' }}>• {c}</div>
                    ))}
                  </div>
                )}
                <div>
                  <h3 style={{ fontSize: '15px', marginBottom: '8px' }}>Stages ({selectedPipeline.stages.filter(s => s.status === 'passed').length}/{selectedPipeline.stages.length})</h3>
                  {selectedPipeline.stages.map((s, i) => (
                    <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '8px 0', borderBottom: '1px solid #333' }}>
                      <StageIcon status={s.status} />
                      <div style={{ flex: 1 }}>
                        <div style={{ fontSize: '14px', color: '#CCC' }}>{s.stage}</div>
                        <div style={{ fontSize: '11px', color: '#666' }}>
                          {s.agent} {s.duration_ms > 0 && `· ${s.duration_ms}ms`} {s.retry_count > 0 && `· retry ${s.retry_count}`}
                        </div>
                      </div>
                      <div style={{ fontSize: '12px', ...statusBadge(s.status) }}>{s.status}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '300px', color: '#666' }}>
              Select a pipeline to view details
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function StageIcon({ status }) {
  const icons = { passed: '✓', failed: '✗', running: '→', pending: '○', skipped: '—', retrying: '↻' };
  const colors = { passed: '#22C55E', failed: '#EF4444', running: '#4F46E5', pending: '#666', skipped: '#444', retrying: '#FFA500' };
  return <span style={{ fontSize: '18px', color: colors[status] || '#666', fontWeight: 700, width: '24px', textAlign: 'center' }}>{icons[status] || '?'}</span>;
}

function CreatePipelineForm({ onCreate }) {
  const [form, setForm] = useState({ title: '', description: '', project_type: 'generic', priority: 'medium', constraints: [] });
  const [constraintInput, setConstraintInput] = useState('');

  return (
    <form onSubmit={(e) => { e.preventDefault(); onCreate(form); }} style={{ background: '#1A1A1E', padding: '20px', borderRadius: '10px', marginBottom: '24px' }}>
      <h2 style={{ fontSize: '18px', marginBottom: '12px' }}>New Feature Pipeline</h2>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
        <input placeholder="Feature Title" value={form.title} onChange={(e) => setForm({...form, title: e.target.value})} style={inputStyle} required />
        <select value={form.priority} onChange={(e) => setForm({...form, priority: e.target.value})} style={inputStyle}>
          <option value="low">Low</option><option value="medium">Medium</option><option value="high">High</option><option value="critical">Critical</option>
        </select>
      </div>
      <textarea placeholder="Feature Description" value={form.description} onChange={(e) => setForm({...form, description: e.target.value})} style={{...inputStyle, width: '100%', minHeight: '80px', marginTop: '12px', resize: 'vertical'}} required />
      <div style={{ marginTop: '12px' }}>
        <input placeholder="Add constraint (press Enter)" value={constraintInput}
          onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); if (constraintInput.trim()) { setForm({...form, constraints: [...form.constraints, constraintInput.trim()]}); setConstraintInput(''); } } }}
          onChange={(e) => setConstraintInput(e.target.value)} style={inputStyle} />
        <div style={{ display: 'flex', gap: '6px', marginTop: '4px', flexWrap: 'wrap' }}>
          {form.constraints.map((c, i) => (<span key={i} style={{ padding: '2px 8px', fontSize: '11px', background: '#3A2A1A', borderRadius: '4px', color: '#FFA500' }}>{c}</span>))}
        </div>
      </div>
      <button type="submit" style={{ marginTop: '12px', ...btnPrimary }}>Start Pipeline</button>
    </form>
  );
}

function evtColor(type) {
  if (type.includes('passed')) return '#22C55E';
  if (type.includes('failed')) return '#EF4444';
  if (type.includes('started')) return '#4F46E5';
  if (type.includes('completed')) return '#22C55E';
  if (type.includes('cancelled')) return '#FFA500';
  return '#888';
}

function statusBadge(status) {
  const styles = {
    passed: { background: '#0D3D1A', color: '#22C55E' },
    failed: { background: '#3D1A0D', color: '#EF4444' },
    running: { background: '#0D1A3D', color: '#4F46E5' },
    pending: { background: '#2A2A2E', color: '#888' },
    completed: { background: '#0D3D1A', color: '#22C55E' },
    cancelled: { background: '#3D2A0D', color: '#FFA500' },
    retrying: { background: '#3D2A0D', color: '#FFA500' },
  };
  return { padding: '2px 8px', borderRadius: '4px', fontSize: '11px', ...(styles[status] || { background: '#2A2A2E', color: '#888' }) };
}

const inputStyle = { padding: '8px 12px', background: '#0D0D0F', border: '1px solid #333', borderRadius: '6px', color: '#fff', fontSize: '14px' };
const btnPrimary = { padding: '8px 16px', background: '#4F46E5', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer' };
const btnSmall = { padding: '4px 12px', background: '#4F46E5', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '12px' };

export default FeaturePipeline;
