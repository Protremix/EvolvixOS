import React, { useState, useEffect, useCallback } from 'react';
import deploymentService from '../services/deploymentService';

function Deployment() {
  const [tab, setTab] = useState('overview');
  const [deployments, setDeployments] = useState([]);
  const [environments, setEnvironments] = useState([]);
  const [stats, setStats] = useState(null);
  const [workflows, setWorkflows] = useState([]);
  const [createForm, setCreateForm] = useState({ component: 'blockchain', target: 'staging', version: '', commit_sha: '', commit_message: '', branch: 'main', previous_version: '' });

  const fetchAll = useCallback(async () => {
    try {
      const [depsResp, envsResp, statsResp, wfResp] = await Promise.all([
        deploymentService.list({ limit: 50 }),
        deploymentService.environments(),
        deploymentService.stats(),
        deploymentService.workflows(),
      ]);
      setDeployments(depsResp.data || []);
      setEnvironments(envsResp.data || []);
      setStats(statsResp.data || {});
      setWorkflows(wfResp.data || []);
    } catch (err) { console.error(err); }
  }, []);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  const handleCreate = async () => {
    try {
      await deploymentService.create(createForm);
      setCreateForm({ ...createForm, version: '', commit_sha: '', commit_message: '', previous_version: '' });
      fetchAll();
    } catch (err) { console.error(err); }
  };

  const statusColor = { success: '#22C55E', failed: '#EF4444', pending: '#FFA500', in_progress: '#4F46E5', cancelled: '#888', rollback: '#A855F7' };
  const panel = { background: '#1A1A1E', borderRadius: '10px', border: '1px solid #333', padding: '14px' };
  const btn = { padding: '8px 16px', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '13px', color: '#fff' };
  const input = { padding: '8px 12px', background: '#0D0D0F', border: '1px solid #333', borderRadius: '6px', color: '#fff', fontSize: '13px', width: '100%' };

  return (
    <div style={{ padding: '24px' }}>
      <h1 style={{ fontSize: '28px', fontWeight: 700, marginBottom: '4px' }}>🚀 Deployment</h1>
      <p style={{ color: '#888', marginBottom: '20px' }}>Manage deployments across environments</p>

      <div style={{ display: 'flex', gap: '4px', marginBottom: '16px' }}>
        {['overview', 'deployments', 'create', 'environments', 'workflows'].map(t => (
          <button key={t} onClick={() => setTab(t)} style={{ ...btn, background: tab === t ? '#4F46E5' : '#1A1A1E', textTransform: 'capitalize' }}>{t}</button>
        ))}
      </div>

      {tab === 'overview' && stats && (
        <div style={{ display: 'grid', gap: '8px' }}>
          <div style={{ display: 'flex', gap: '8px' }}>
            {[
              { label: 'Total', value: stats.total_deployments },
              { label: 'Success Rate', value: `${stats.success_rate}%` },
              { label: 'Avg Duration', value: `${stats.avg_duration_seconds}s` },
            ].map(s => (
              <div key={s.label} style={{ ...panel, flex: 1, textAlign: 'center' }}>
                <div style={{ fontSize: '10px', color: '#888' }}>{s.label}</div>
                <div style={{ fontSize: '18px', fontWeight: 700 }}>{s.value}</div>
              </div>
            ))}
          </div>
          {stats.by_status && Object.keys(stats.by_status).length > 0 && (
            <div style={panel}>
              <div style={{ fontSize: '12px', fontWeight: 600, marginBottom: '8px' }}>By Status</div>
              {Object.entries(stats.by_status).map(([k, v]) => (
                <div key={k} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', padding: '2px 0' }}>
                  <span style={{ color: statusColor[k] || '#888' }}>{k}</span>
                  <span>{v}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {tab === 'deployments' && (
        <div style={{ display: 'grid', gap: '6px' }}>
          {deployments.map((d, i) => (
            <div key={i} style={panel}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ fontSize: '12px', fontWeight: 600 }}>{d.component} → {d.target}</div>
                <span style={{ fontSize: '10px', padding: '2px 8px', borderRadius: '4px', background: (statusColor[d.status] || '#888') + '22', color: statusColor[d.status] || '#888', fontWeight: 600 }}>{d.status}</span>
              </div>
              <div style={{ fontSize: '11px', color: '#888', marginTop: '4px' }}>v{d.version} | {d.commit_sha?.substring(0, 7) || '—'}</div>
              <div style={{ fontSize: '10px', color: '#666', marginTop: '2px' }}>{d.commit_message || '—'}</div>
              {d.rollback_available && <div style={{ fontSize: '10px', color: '#A855F7', marginTop: '2px' }}>↩ Rollback available (prev: {d.previous_version})</div>}
            </div>
          ))}
          {deployments.length === 0 && <div style={{ fontSize: '12px', color: '#888' }}>No deployments yet</div>}
        </div>
      )}

      {tab === 'create' && (
        <div style={{ ...panel, maxWidth: '500px' }}>
          <div style={{ fontSize: '14px', fontWeight: 600, marginBottom: '12px' }}>Create Deployment</div>
          <div style={{ display: 'grid', gap: '8px' }}>
            <select value={createForm.component} onChange={e => setCreateForm({ ...createForm, component: e.target.value })} style={input}>
              <option value="blockchain">Blockchain</option>
              <option value="evolvixos_backend">EvolvixOS Backend</option>
              <option value="evolvixos_frontend">EvolvixOS Frontend</option>
              <option value="explorer">Explorer</option>
              <option value="wallet_android">Wallet Android</option>
              <option value="wallet_web">Wallet Web</option>
              <option value="bridge">Bridge</option>
              <option value="sdk">SDK</option>
              <option value="docs">Docs</option>
            </select>
            <select value={createForm.target} onChange={e => setCreateForm({ ...createForm, target: e.target.value })} style={input}>
              <option value="staging">Staging</option>
              <option value="production">Production</option>
              <option value="mainnet">Mainnet</option>
            </select>
            <input value={createForm.version} onChange={e => setCreateForm({ ...createForm, version: e.target.value })} placeholder="Version (e.g., v2.0.0)" style={input} />
            <input value={createForm.commit_sha} onChange={e => setCreateForm({ ...createForm, commit_sha: e.target.value })} placeholder="Commit SHA" style={input} />
            <input value={createForm.commit_message} onChange={e => setCreateForm({ ...createForm, commit_message: e.target.value })} placeholder="Commit message" style={input} />
            <input value={createForm.branch} onChange={e => setCreateForm({ ...createForm, branch: e.target.value })} placeholder="Branch" style={input} />
            <input value={createForm.previous_version} onChange={e => setCreateForm({ ...createForm, previous_version: e.target.value })} placeholder="Previous version (for rollback)" style={input} />
            <button onClick={handleCreate} style={{ ...btn, background: '#4F46E5' }}>Create Deployment</button>
          </div>
        </div>
      )}

      {tab === 'environments' && (
        <div style={{ display: 'grid', gap: '8px' }}>
          {environments.map((env, i) => (
            <div key={i} style={panel}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <div style={{ fontSize: '14px', fontWeight: 600 }}>{env.name}</div>
                <span style={{ fontSize: '10px', padding: '2px 8px', borderRadius: '4px', background: (statusColor[env.status === 'healthy' ? 'success' : env.status === 'degraded' ? 'pending' : 'failed']) + '22', color: statusColor[env.status === 'healthy' ? 'success' : env.status === 'degraded' ? 'pending' : 'failed'], fontWeight: 600 }}>{env.status}</span>
              </div>
              <div style={{ fontSize: '11px', color: '#4F46E5' }}>{env.url}</div>
              <div style={{ fontSize: '10px', color: '#888', marginTop: '4px' }}>Version: {env.version || '—'}</div>
              <div style={{ fontSize: '10px', color: '#888', marginTop: '4px' }}>Components:</div>
              {Object.entries(env.components || {}).map(([k, v]) => (
                <div key={k} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', padding: '1px 0 1px 8px' }}>
                  <span style={{ color: '#888' }}>{k}</span>
                  <span style={{ color: v === 'deployed' ? '#22C55E' : v === 'not_deployed' ? '#666' : '#FFA500' }}>{v}</span>
                </div>
              ))}
            </div>
          ))}
        </div>
      )}

      {tab === 'workflows' && (
        <div style={{ display: 'grid', gap: '8px' }}>
          {workflows.map((w, i) => (
            <div key={i} style={panel}>
              <div style={{ fontSize: '13px', fontWeight: 600 }}>{w.name}</div>
              <div style={{ fontSize: '11px', color: '#888', marginTop: '4px' }}>{w.description}</div>
              <div style={{ display: 'flex', gap: '8px', marginTop: '6px', fontSize: '10px' }}>
                <span style={{ padding: '2px 6px', borderRadius: '4px', background: '#4F46E522', color: '#4F46E5' }}>{w.trigger}</span>
                {w.targets?.map(t => (
                  <span key={t} style={{ padding: '2px 6px', borderRadius: '4px', background: '#22C55E22', color: '#22C55E' }}>{t}</span>
                ))}
              </div>
              <div style={{ fontSize: '10px', color: '#666', marginTop: '4px' }}>File: {w.file}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default Deployment;
