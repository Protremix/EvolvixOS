import React, { useState, useEffect, useCallback } from 'react';
import agentConfigService from '../services/agentConfigService';

function AgentConfig() {
  const [agents, setAgents] = useState([]);
  const [models, setModels] = useState([]);
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [effectiveConfig, setEffectiveConfig] = useState(null);
  const [editConfig, setEditConfig] = useState(null);
  const [projectId, setProjectId] = useState('');
  const [showGlobal, setShowGlobal] = useState(false);
  const [loading, setLoading] = useState(true);

  const fetchAgents = useCallback(async () => {
    try {
      const [agentsResp, modelsResp] = await Promise.all([
        agentConfigService.listAgents(),
        agentConfigService.listModels(),
      ]);
      setAgents(agentsResp.data);
      setModels(modelsResp.data);
      if (agentsResp.data.length > 0) setSelectedAgent(agentsResp.data[0].agent_name);
    } catch (err) { console.error('Failed', err); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchAgents(); }, [fetchAgents]);

  useEffect(() => {
    if (!selectedAgent) return;
    agentConfigService.effectiveConfig(selectedAgent, projectId || undefined)
      .then(r => { setEffectiveConfig(r.data); setEditConfig(r.data); })
      .catch(err => console.error(err));
  }, [selectedAgent, projectId]);

  const handleSave = async () => {
    try {
      if (showGlobal) {
        await agentConfigService.setGlobalOverride(selectedAgent, editConfig);
      } else if (projectId) {
        await agentConfigService.setProjectConfig(projectId, selectedAgent, editConfig);
      }
      alert('Configuration saved!');
      const r = await agentConfigService.effectiveConfig(selectedAgent, projectId || undefined);
      setEffectiveConfig(r.data);
    } catch (err) { alert('Failed to save: ' + (err.response?.data?.detail || err.message)); }
  };

  if (loading) return <div style={{ padding: '24px', color: '#888' }}>Loading agent configs...</div>;

  return (
    <div style={{ padding: '24px' }}>
      <h1 style={{ fontSize: '28px', fontWeight: 700, margin: '0 0 8px' }}>Agent Configuration</h1>
      <p style={{ color: '#888', marginBottom: '24px' }}>Configure AI agent behavior per project or globally</p>

      <div style={{ display: 'grid', gridTemplateColumns: '220px 1fr', gap: '24px' }}>
        {/* Agent List */}
        <div>
          <h2 style={{ fontSize: '14px', color: '#888', marginBottom: '8px' }}>Agents ({agents.length})</h2>
          {agents.map(a => (
            <button key={a.agent_name} onClick={() => setSelectedAgent(a.agent_name)}
              style={selectedAgent === a.agent_name ? agentActive : agentBtn}>
              {a.agent_name.replace(/_/g, ' ')}
            </button>
          ))}
        </div>

        {/* Config Panel */}
        <div>
          {effectiveConfig && (
            <div style={{ background: '#1A1A1E', borderRadius: '10px', padding: '24px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '16px' }}>
                <h2 style={{ fontSize: '20px', textTransform: 'capitalize' }}>{selectedAgent?.replace(/_/g, ' ')}</h2>
                <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                  <input placeholder="Project ID (optional)" value={projectId}
                    onChange={e => setProjectId(e.target.value)} style={inputStyle} />
                  <label style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '13px', color: '#888' }}>
                    <input type="checkbox" checked={showGlobal} onChange={e => setShowGlobal(e.target.checked)} /> Global
                  </label>
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div>
                  <label style={labelStyle}>Model</label>
                  <select value={editConfig?.model || ''} onChange={e => setEditConfig({...editConfig, model: e.target.value})} style={inputStyle}>
                    {models.map(m => <option key={m} value={m}>{m}</option>)}
                  </select>
                </div>
                <div>
                  <label style={labelStyle}>Temperature ({editConfig?.temperature})</label>
                  <input type="range" min="0" max="2" step="0.1" value={editConfig?.temperature || 0.3}
                    onChange={e => setEditConfig({...editConfig, temperature: parseFloat(e.target.value)})} style={{ width: '100%' }} />
                </div>
                <div>
                  <label style={labelStyle}>Max Retries</label>
                  <input type="number" min="0" max="10" value={editConfig?.max_retries ?? 2}
                    onChange={e => setEditConfig({...editConfig, max_retries: parseInt(e.target.value) || 0})} style={inputStyle} />
                </div>
                <div>
                  <label style={labelStyle}>Timeout (seconds)</label>
                  <input type="number" min="10" max="600" value={editConfig?.timeout_seconds ?? 120}
                    onChange={e => setEditConfig({...editConfig, timeout_seconds: parseInt(e.target.value) || 120})} style={inputStyle} />
                </div>
              </div>

              <div style={{ marginTop: '12px' }}>
                <label style={labelStyle}>System Prompt Prefix</label>
                <textarea value={editConfig?.system_prompt_prefix || ''} placeholder="Additional context to prepend to agent's system prompt..."
                  onChange={e => setEditConfig({...editConfig, system_prompt_prefix: e.target.value})}
                  style={{ ...inputStyle, width: '100%', minHeight: '60px', resize: 'vertical' }} />
              </div>

              <div style={{ marginTop: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <input type="checkbox" checked={editConfig?.enabled ?? true}
                    onChange={e => setEditConfig({...editConfig, enabled: e.target.checked})} />
                  <span style={{ fontSize: '14px' }}>Enabled</span>
                </label>
              </div>

              <button onClick={handleSave} style={{ marginTop: '16px', ...btnPrimary }}>
                Save {showGlobal ? 'Global Override' : projectId ? `Project Config (${projectId})` : 'Configuration'}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

const inputStyle = { padding: '8px 12px', background: '#0D0D0F', border: '1px solid #333', borderRadius: '6px', color: '#fff', fontSize: '14px', width: '100%' };
const labelStyle = { display: 'block', fontSize: '12px', color: '#888', marginBottom: '4px' };
const btnPrimary = { padding: '8px 16px', background: '#4F46E5', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer' };
const agentBtn = { display: 'block', width: '100%', textAlign: 'left', padding: '8px 12px', background: 'transparent', border: 'none', borderRadius: '6px', color: '#888', cursor: 'pointer', fontSize: '13px', marginBottom: '4px' };
const agentActive = { ...agentBtn, background: '#4F46E5', color: '#fff' };

export default AgentConfig;
