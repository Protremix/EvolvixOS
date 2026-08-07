import React, { useState, useEffect, useCallback } from 'react';
import evolvixosInfraService from '../services/evolvixosInfraService';

function EvolvixOSInfra() {
  const [tab, setTab] = useState('overview');
  const [dashboard, setDashboard] = useState(null);
  const [scripts, setScripts] = useState({});
  const [selectedScript, setSelectedScript] = useState(null);

  const fetchData = useCallback(async () => {
    try {
      const [dash, scr] = await Promise.all([
        evolvixosInfraService.dashboard(),
        evolvixosInfraService.scripts(),
      ]);
      setDashboard(dash.data || null);
      setScripts(scr.data || {});
    } catch (err) { console.error(err); }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const panel = { background: '#1A1A1E', borderRadius: '10px', border: '1px solid #333', padding: '14px' };
  const btn = { padding: '6px 12px', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '12px', color: '#fff' };
  const statusColor = { pending: '#888', provisioning: '#4F46E5', configuring: '#FFA500', deploying: '#F97316', live: '#22C55E', error: '#EF4444' };
  const compColor = { frontend: '#4F46E5', backend: '#22C55E', database: '#A855F7', redis: '#EF4444', nginx: '#06B6D4', monitoring: '#FFA500', docker: '#3B82F6' };

  return (
    <div style={{ padding: '24px' }}>
      <h1 style={{ fontSize: '28px', fontWeight: 700, marginBottom: '4px' }}>🌐 EvolvixOS Infrastructure</h1>
      <p style={{ color: '#888', marginBottom: '12px' }}>Separate domain & server for EvolvixOS platform</p>

      {dashboard && (
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '12px' }}>
          <div style={{ ...panel, flex: '2 1 200px' }}>
            <div style={{ fontSize: '10px', color: '#888' }}>Domain</div>
            <div style={{ fontSize: '20px', fontWeight: 700, color: '#4F46E5' }}>evolvixos.com</div>
          </div>
          <div style={{ ...panel, flex: '1 1 100px', textAlign: 'center' }}>
            <div style={{ fontSize: '10px', color: '#888' }}>Components</div>
            <div style={{ fontSize: '16px', fontWeight: 700 }}>{dashboard.components?.length || 0}</div>
          </div>
          <div style={{ ...panel, flex: '1 1 100px', textAlign: 'center' }}>
            <div style={{ fontSize: '10px', color: '#888' }}>Subdomains</div>
            <div style={{ fontSize: '16px', fontWeight: 700 }}>{dashboard.dns_records?.length || 0}</div>
          </div>
          <div style={{ ...panel, flex: '1 1 100px', textAlign: 'center' }}>
            <div style={{ fontSize: '10px', color: '#888' }}>Steps</div>
            <div style={{ fontSize: '16px', fontWeight: 700 }}>{dashboard.steps?.length || 0}</div>
          </div>
          <div style={{ ...panel, flex: '1 1 100px', textAlign: 'center' }}>
            <div style={{ fontSize: '10px', color: '#888' }}>Server IP</div>
            <div style={{ fontSize: '14px', fontWeight: 700, color: dashboard.progress?.server_ip === 'PLACEHOLDER_IP' ? '#FFA500' : '#22C55E' }}>
              {dashboard.progress?.server_ip === 'PLACEHOLDER_IP' ? 'Not set' : dashboard.progress?.server_ip}
            </div>
          </div>
        </div>
      )}

      {dashboard?.verdis_connection && (
        <div style={{ ...panel, marginBottom: '12px', borderLeft: '3px solid #22C55E' }}>
          <div style={{ fontSize: '13px', fontWeight: 600 }}>🔗 Verdis Connection</div>
          <div style={{ fontSize: '11px', color: '#888', marginTop: '4px' }}>
            RPC: {dashboard.verdis_connection.rpc_url} | API: {dashboard.verdis_connection.api_url} | Explorer: {dashboard.verdis_connection.explorer_url}
          </div>
        </div>
      )}

      <div style={{ display: 'flex', gap: '4px', marginBottom: '12px', flexWrap: 'wrap' }}>
        {['overview', 'components', 'dns', 'steps', 'scripts'].map(t => (
          <button key={t} onClick={() => setTab(t)} style={{ ...btn, background: tab === t ? '#4F46E5' : '#1A1A1E', textTransform: 'capitalize' }}>{t}</button>
        ))}
      </div>

      {tab === 'overview' && dashboard && (
        <div style={{ display: 'grid', gap: '8px' }}>
          <div style={panel}>
            <div style={{ fontSize: '14px', fontWeight: 600, marginBottom: '8px' }}>🏗️ Components</div>
            {dashboard.components?.map((c, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', borderBottom: '1px solid #222', fontSize: '12px' }}>
                <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                  <span style={{ fontSize: '9px', padding: '2px 6px', borderRadius: '4px', background: (compColor[c.type] || '#888') + '22', color: compColor[c.type] || '#888' }}>{c.type}</span>
                  <span>{c.name}</span>
                </div>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <span style={{ fontSize: '10px', color: '#888' }}>:{c.port}</span>
                  <span style={{ color: statusColor[c.status] || '#888' }}>● {c.status}</span>
                </div>
              </div>
            ))}
          </div>
          <div style={panel}>
            <div style={{ fontSize: '14px', fontWeight: 600, marginBottom: '8px' }}>📋 Deployment Scripts</div>
            {Object.keys(scripts).map((name, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '3px 0', borderBottom: '1px solid #222', fontSize: '12px' }}>
                <span style={{ cursor: 'pointer', color: '#4F46E5' }} onClick={() => { setSelectedScript(name); setTab('scripts'); }}>📁 {name}</span>
                <span style={{ fontSize: '10px', color: '#666' }}>{scripts[name].length} chars</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {tab === 'components' && dashboard && (
        <div style={{ display: 'grid', gap: '6px' }}>
          {dashboard.components?.map((c, i) => (
            <div key={i} style={{ ...panel, borderLeft: `3px solid ${compColor[c.type] || '#888'}` }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <div style={{ fontSize: '13px', fontWeight: 600 }}>{c.name}</div>
                <span style={{ fontSize: '9px', padding: '2px 6px', borderRadius: '4px', background: (statusColor[c.status] || '#888') + '22', color: statusColor[c.status] || '#888' }}>{c.status}</span>
              </div>
              <div style={{ fontSize: '11px', color: '#888', marginTop: '4px' }}>Port: {c.port} | Image: {c.docker_image}</div>
              {c.health_url && <div style={{ fontSize: '10px', color: '#666', marginTop: '4px' }}>Health: {c.health_url}</div>}
              {c.environment_vars?.length > 0 && (
                <details style={{ marginTop: '4px' }}>
                  <summary style={{ fontSize: '10px', color: '#4F46E5', cursor: 'pointer' }}>Env vars ({c.environment_vars.length})</summary>
                  {c.environment_vars.map((v, j) => <div key={j} style={{ fontSize: '10px', color: '#666', fontFamily: 'monospace' }}>{v}</div>)}
                </details>
              )}
            </div>
          ))}
        </div>
      )}

      {tab === 'dns' && dashboard && (
        <div style={{ display: 'grid', gap: '4px' }}>
          {dashboard.dns_records?.map((d, i) => (
            <div key={i} style={panel}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <span style={{ fontSize: '9px', padding: '2px 6px', borderRadius: '4px', background: '#4F46E522', color: '#4F46E5' }}>{d.record_type}</span>
                  <span style={{ fontSize: '13px', fontWeight: 600 }}>{d.full_domain}</span>
                </div>
                <span style={{ fontSize: '12px', color: '#22C55E' }}>→ {d.target}</span>
              </div>
              <div style={{ fontSize: '10px', color: '#888', marginTop: '4px' }}>{d.description} | TTL: {d.ttl}s</div>
            </div>
          ))}
        </div>
      )}

      {tab === 'steps' && dashboard && (
        <div style={{ display: 'grid', gap: '4px' }}>
          {dashboard.steps?.map((s, i) => (
            <div key={i} style={{ ...panel, opacity: s.status === 'live' ? 0.6 : 1, borderLeft: `3px solid ${statusColor[s.status] || '#888'}` }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                  <span style={{ width: '24px', height: '24px', borderRadius: '50%', background: s.status === 'live' ? '#22C55E' : '#333', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '12px', fontWeight: 600 }}>{s.order}</span>
                  <div>
                    <div style={{ fontSize: '13px', fontWeight: s.status === 'live' ? '400' : '600' }}>{s.name}</div>
                    <div style={{ fontSize: '11px', color: '#888' }}>{s.description}</div>
                  </div>
                </div>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <span style={{ fontSize: '10px', color: '#888' }}>⏱ {s.expected_time}</span>
                  <span style={{ fontSize: '9px', padding: '2px 6px', borderRadius: '4px', background: (statusColor[s.status] || '#888') + '22', color: statusColor[s.status] || '#888' }}>{s.status}</span>
                </div>
              </div>
              {s.command && <div style={{ fontSize: '10px', color: '#A855F7', marginTop: '4px', fontFamily: 'monospace' }}>$ {s.command}</div>}
            </div>
          ))}
        </div>
      )}

      {tab === 'scripts' && (
        <div style={{ display: 'grid', gap: '8px' }}>
          {Object.entries(scripts).map(([name, content], i) => (
            <div key={i} style={panel}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <div style={{ fontSize: '13px', fontWeight: 600 }}>📁 {name}</div>
                <span style={{ fontSize: '10px', color: '#666' }}>{content.length} chars</span>
              </div>
              <details open={selectedScript === name}>
                <summary style={{ fontSize: '11px', color: '#4F46E5', cursor: 'pointer' }}>View content</summary>
                <pre style={{ fontSize: '10px', color: '#aaa', marginTop: '8px', background: '#0D0D0F', padding: '8px', borderRadius: '6px', overflow: 'auto', maxHeight: '300px' }}>{content}</pre>
              </details>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default EvolvixOSInfra;
