import React, { useState, useEffect, useCallback } from 'react';
import multiProjectService from '../services/multiProjectService';

function MultiProject() {
  const [projects, setProjects] = useState([]);
  const [stats, setStats] = useState(null);
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState('');
  const [newType, setNewType] = useState('web_backend');

  const fetchAll = useCallback(async () => {
    try {
      const [pResp, sResp] = await Promise.all([
        multiProjectService.list(),
        multiProjectService.stats(),
      ]);
      setProjects(pResp.data);
      setStats(sResp.data);
    } catch (err) { console.error(err); }
  }, []);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  const handleCreate = async () => {
    try {
      await multiProjectService.register({ name: newName, type: newType });
      setNewName(''); setShowCreate(false); fetchAll();
    } catch (err) { console.error(err); }
  };

  const handleAction = async (id, action) => {
    try {
      if (action === 'archive') await multiProjectService.archive(id);
      if (action === 'pause') await multiProjectService.pause(id);
      if (action === 'resume') await multiProjectService.resume(id);
      fetchAll();
    } catch (err) { console.error(err); }
  };

  const typeIcons = { blockchain: '⛓️', web_backend: '🌐', frontend: '🎨', mobile: '📱', infrastructure: '🔧', ai_ml: '🤖', generic: '📦' };

  return (
    <div style={{ padding: '24px' }}>
      <h1 style={{ fontSize: '28px', fontWeight: 700, marginBottom: '4px' }}>📂 Multi-Project</h1>
      <p style={{ color: '#888', marginBottom: '24px' }}>Manage multiple projects with type-specific adapters</p>

      {stats && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(120px, 1fr))', gap: '8px', marginBottom: '20px' }}>
          <Stat label="Total" value={stats.total_projects} />
          <Stat label="Active" value={stats.active} color="#22C55E" />
          <Stat label="Paused" value={stats.paused} color="#FFA500" />
          <Stat label="Archived" value={stats.archived} color="#888" />
          <Stat label="Types" value={Object.keys(stats.by_type || {}).length} color="#4F46E5" />
        </div>
      )}

      <button onClick={() => setShowCreate(!showCreate)} style={{ padding: '8px 16px', background: '#4F46E5', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '13px', marginBottom: '16px' }}>
        + Register Project
      </button>

      {showCreate && (
        <div style={{ ...panel, marginBottom: '16px' }}>
          <input value={newName} onChange={e => setNewName(e.target.value)} placeholder="Project name" style={{ ...input, marginRight: '8px' }} />
          <select value={newType} onChange={e => setNewType(e.target.value)} style={{ ...input, marginRight: '8px' }}>
            <option value="blockchain">Blockchain</option>
            <option value="web_backend">Web Backend</option>
            <option value="frontend">Frontend</option>
            <option value="mobile">Mobile</option>
            <option value="infrastructure">Infrastructure</option>
            <option value="ai_ml">AI/ML</option>
            <option value="generic">Generic</option>
          </select>
          <button onClick={handleCreate} style={{ ...btn, background: '#22C55E' }}>Create</button>
        </div>
      )}

      <div style={{ display: 'grid', gap: '8px' }}>
        {projects.map(p => (
          <div key={p.id} style={{ ...panel }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <div>
                <div style={{ fontSize: '16px', fontWeight: 600 }}>
                  {typeIcons[p.type] || '📦'} {p.name}
                </div>
                <div style={{ fontSize: '12px', color: '#888', marginTop: '2px' }}>{p.description}</div>
                <div style={{ display: 'flex', gap: '4px', marginTop: '6px' }}>
                  <Badge color="#4F46E5">{p.type}</Badge>
                  <Badge color={p.status === 'active' ? '#22C55E' : p.status === 'paused' ? '#FFA500' : '#888'}>{p.status}</Badge>
                  <Badge color={p.health_status === 'healthy' ? '#22C55E' : p.health_status === 'degraded' ? '#FFA500' : '#888'}>{p.health_status}</Badge>
                  {p.domain && <Badge color="#666">{p.domain}</Badge>}
                </div>
                {p.config && Object.keys(p.config).length > 0 && (
                  <div style={{ fontSize: '11px', color: '#666', marginTop: '6px' }}>
                    {Object.entries(p.config).slice(0, 3).map(([k, v]) => `${k}: ${v}`).join(' · ')}
                  </div>
                )}
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                {p.status === 'active' && <button onClick={() => handleAction(p.id, 'pause')} style={{ ...btnSmall, background: '#FFA500' }}>Pause</button>}
                {p.status === 'paused' && <button onClick={() => handleAction(p.id, 'resume')} style={{ ...btnSmall, background: '#22C55E' }}>Resume</button>}
                {p.status !== 'archived' && <button onClick={() => handleAction(p.id, 'archive')} style={{ ...btnSmall, background: '#666' }}>Archive</button>}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function Stat({ label, value, color }) {
  return (
    <div style={{ background: '#1A1A1E', borderRadius: '8px', padding: '10px', border: '1px solid #333' }}>
      <div style={{ fontSize: '10px', color: '#888' }}>{label}</div>
      <div style={{ fontSize: '18px', fontWeight: 700, color: color || '#fff', marginTop: '2px' }}>{value}</div>
    </div>
  );
}
function Badge({ color, children }) {
  return <span style={{ fontSize: '10px', padding: '2px 6px', borderRadius: '4px', background: color + '22', color, fontWeight: 600 }}>{children}</span>;
}
const panel = { background: '#1A1A1E', borderRadius: '10px', border: '1px solid #333', padding: '12px 16px' };
const btn = { padding: '6px 14px', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '13px' };
const btnSmall = { padding: '4px 10px', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '11px' };
const input = { padding: '6px 10px', background: '#0D0D0F', border: '1px solid #333', borderRadius: '6px', color: '#fff', fontSize: '13px', marginBottom: '8px' };

export default MultiProject;
