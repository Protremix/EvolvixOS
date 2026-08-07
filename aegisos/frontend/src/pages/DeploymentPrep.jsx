import React, { useState, useEffect, useCallback } from 'react';
import deployService from '../services/deployService';

function DeploymentPrep() {
  const [tab, setTab] = useState('overview');
  const [dashboard, setDashboard] = useState(null);
  const [progress, setProgress] = useState(null);
  const [steps, setSteps] = useState([]);
  const [scripts, setScripts] = useState([]);
  const [dns, setDns] = useState([]);
  const [ssl, setSsl] = useState([]);
  const [selectedScript, setSelectedScript] = useState(null);

  const fetchData = useCallback(async () => {
    try {
      const [dash, prog, stp, scr, dn, ss] = await Promise.all([
        deployService.dashboard(),
        deployService.progress(),
        deployService.steps(),
        deployService.scripts(),
        deployService.dns(),
        deployService.ssl(),
      ]);
      setDashboard(dash.data || null);
      setProgress(prog.data || null);
      setSteps(stp.data || []);
      setScripts(scr.data || []);
      setDns(dn.data || []);
      setSsl(ss.data || []);
    } catch (err) { console.error(err); }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleStepComplete = async (id) => {
    try { await deployService.updateStepStatus(id, 'completed'); fetchData(); } catch (e) { console.error(e); }
  };

  const panel = { background: '#1A1A1E', borderRadius: '10px', border: '1px solid #333', padding: '14px' };
  const btn = { padding: '8px 16px', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '13px', color: '#fff' };
  const statusColor = { pending: '#888', ready: '#4F46E5', running: '#FFA500', completed: '#22C55E', failed: '#EF4444' };
  const scriptTypeColor = { dns: '#4F46E5', ssl: '#22C55E', deploy: '#F97316', hardening: '#EF4444', monitoring: '#A855F7', backup: '#06B6D4', rollback: '#FFA500', health_check: '#3B82F6' };

  return (
    <div style={{ padding: '24px' }}>
      <h1 style={{ fontSize: '28px', fontWeight: 700, marginBottom: '4px' }}>🚀 Deployment Preparation</h1>
      <p style={{ color: '#888', marginBottom: '12px' }}>Scripts, DNS, SSL, and step-by-step deployment guide</p>

      {progress && (
        <div style={{ ...panel, marginBottom: '12px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <div style={{ fontSize: '14px', fontWeight: 600 }}>Deployment Progress</div>
              <div style={{ fontSize: '12px', color: '#888' }}>{progress.completed} / {progress.total} steps completed ({progress.percentage}%)</div>
            </div>
            <div style={{ fontSize: '32px', fontWeight: 700, color: progress.percentage >= 100 ? '#22C55E' : progress.percentage >= 50 ? '#FFA500' : '#4F46E5' }}>
              {progress.percentage}%
            </div>
          </div>
          {progress.next_step && (
            <div style={{ fontSize: '12px', color: '#4F46E5', marginTop: '8px' }}>
              Next: {progress.next_step.order}. {progress.next_step.name} — {progress.next_step.description}
            </div>
          )}
        </div>
      )}

      <div style={{ display: 'flex', gap: '4px', marginBottom: '12px', flexWrap: 'wrap' }}>
        {['overview', 'steps', 'scripts', 'dns', 'ssl'].map(t => (
          <button key={t} onClick={() => setTab(t)} style={{ ...btn, background: tab === t ? '#4F46E5' : '#1A1A1E', textTransform: 'capitalize' }}>{t}</button>
        ))}
      </div>

      {tab === 'overview' && dashboard && (
        <div style={{ display: 'grid', gap: '12px' }}>
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            {[
              { l: 'Scripts', v: dashboard.stats?.total_scripts || 0 },
              { l: 'DNS Records', v: dashboard.stats?.total_dns_records || 0 },
              { l: 'SSL Configs', v: dashboard.stats?.total_ssl_configs || 0 },
              { l: 'Steps', v: dashboard.stats?.total_steps || 0 },
              { l: 'Completed', v: dashboard.stats?.completed_steps || 0 },
              { l: 'Pending', v: dashboard.stats?.pending_steps || 0 },
            ].map(s => (
              <div key={s.l} style={{ ...panel, flex: '1 1 100px', textAlign: 'center' }}>
                <div style={{ fontSize: '10px', color: '#888' }}>{s.l}</div>
                <div style={{ fontSize: '16px', fontWeight: 700 }}>{s.v}</div>
              </div>
            ))}
          </div>

          {/* Scripts summary */}
          <div style={panel}>
            <div style={{ fontSize: '14px', fontWeight: 600, marginBottom: '8px' }}>Deployment Scripts</div>
            {scripts.map((s, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', borderBottom: '1px solid #222', fontSize: '12px' }}>
                <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                  <span style={{ fontSize: '9px', padding: '2px 6px', borderRadius: '4px', background: (scriptTypeColor[s.type] || '#888') + '22', color: scriptTypeColor[s.type] || '#888' }}>{s.type}</span>
                  <span>{s.name}</span>
                </div>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <span style={{ fontSize: '10px', color: '#888' }}>📁 {s.filename}</span>
                  <span style={{ color: statusColor[s.status] || '#888' }}>● {s.status}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {tab === 'steps' && (
        <div style={{ display: 'grid', gap: '4px' }}>
          {steps.map((s, i) => (
            <div key={i} style={{ ...panel, opacity: s.status === 'completed' ? 0.6 : 1, borderLeft: `3px solid ${statusColor[s.status] || '#888'}` }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                  <span style={{ width: '24px', height: '24px', borderRadius: '50%', background: s.status === 'completed' ? '#22C55E' : '#333', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '12px', fontWeight: 600 }}>{s.order}</span>
                  <div>
                    <div style={{ fontSize: '13px', fontWeight: s.status === 'completed' ? '400' : '600' }}>{s.name}</div>
                    <div style={{ fontSize: '11px', color: '#888' }}>{s.description}</div>
                  </div>
                </div>
                <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                  <span style={{ fontSize: '10px', color: '#888' }}>⏱ {s.expected_time}</span>
                  <span style={{ fontSize: '9px', padding: '2px 6px', borderRadius: '4px', background: (statusColor[s.status] || '#888') + '22', color: statusColor[s.status] || '#888' }}>{s.status}</span>
                  {s.status !== 'completed' && <button onClick={() => handleStepComplete(s.id)} style={{ ...btn, background: '#4F46E5', fontSize: '10px', padding: '4px 10px' }}>✓</button>}
                </div>
              </div>
              {s.command && <div style={{ fontSize: '10px', color: '#A855F7', marginTop: '4px', fontFamily: 'monospace' }}>$ {s.command}</div>}
              {s.depends_on?.length > 0 && <div style={{ fontSize: '10px', color: '#666', marginTop: '2px' }}>Depends on: steps {s.depends_on.join(', ')}</div>}
            </div>
          ))}
        </div>
      )}

      {tab === 'scripts' && (
        <div style={{ display: 'grid', gap: '8px' }}>
          {scripts.map((s, i) => (
            <div key={i} style={panel}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <div style={{ fontSize: '13px', fontWeight: 600 }}>{s.name}</div>
                <div style={{ display: 'flex', gap: '4px' }}>
                  <span style={{ fontSize: '9px', padding: '2px 6px', borderRadius: '4px', background: (scriptTypeColor[s.type] || '#888') + '22', color: scriptTypeColor[s.type] || '#888' }}>{s.type}</span>
                  {s.requires_root && <span style={{ fontSize: '9px', padding: '2px 6px', borderRadius: '4px', background: '#EF444422', color: '#EF4444' }}>root</span>}
                </div>
              </div>
              <div style={{ fontSize: '11px', color: '#888', marginTop: '4px' }}>{s.description}</div>
              <div style={{ fontSize: '10px', color: '#666', marginTop: '4px' }}>📁 {s.filename} | Timeout: {s.timeout}s | Expected: {s.expected_output}</div>
              <details style={{ marginTop: '8px' }}>
                <summary style={{ fontSize: '11px', color: '#4F46E5', cursor: 'pointer' }}>View script content</summary>
                <pre style={{ fontSize: '10px', color: '#aaa', marginTop: '8px', background: '#0D0D0F', padding: '8px', borderRadius: '6px', overflow: 'auto', maxHeight: '300px' }}>{s.content}</pre>
              </details>
            </div>
          ))}
        </div>
      )}

      {tab === 'dns' && (
        <div style={{ display: 'grid', gap: '4px' }}>
          {dns.map((r, i) => (
            <div key={i} style={panel}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <span style={{ fontSize: '9px', padding: '2px 6px', borderRadius: '4px', background: '#4F46E522', color: '#4F46E5' }}>{r.type}</span>
                  <span style={{ fontSize: '13px', fontWeight: 600 }}>{r.name}</span>
                </div>
                <span style={{ fontSize: '12px', color: '#22C55E' }}>→ {r.value}</span>
              </div>
              <div style={{ fontSize: '10px', color: '#888', marginTop: '4px' }}>{r.description} | TTL: {r.ttl}s</div>
            </div>
          ))}
        </div>
      )}

      {tab === 'ssl' && (
        <div style={{ display: 'grid', gap: '4px' }}>
          {ssl.map((c, i) => (
            <div key={i} style={panel}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <div style={{ fontSize: '13px', fontWeight: 600 }}>🔒 {c.domain}</div>
                <div style={{ display: 'flex', gap: '4px' }}>
                  <span style={{ fontSize: '9px', padding: '2px 6px', borderRadius: '4px', background: '#22C55E22', color: '#22C55E' }}>{c.issuer}</span>
                  {c.auto_renew && <span style={{ fontSize: '9px', padding: '2px 6px', borderRadius: '4px', background: '#4F46E522', color: '#4F46E5' }}>Auto-renew</span>}
                </div>
              </div>
              <div style={{ fontSize: '10px', color: '#888', marginTop: '4px' }}>
                📁 {c.cert_path}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default DeploymentPrep;
