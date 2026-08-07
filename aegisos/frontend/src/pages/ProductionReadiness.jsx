import React, { useState, useEffect, useCallback } from 'react';
import readinessService from '../services/readinessService';

function ProductionReadiness() {
  const [tab, setTab] = useState('overview');
  const [dashboard, setDashboard] = useState(null);
  const [findings, setFindings] = useState([]);
  const [checks, setChecks] = useState([]);
  const [checklist, setChecklist] = useState([]);
  const [loadTests, setLoadTests] = useState([]);
  const [autoRefresh, setAutoRefresh] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const [dash, fnd, chk, cl] = await Promise.all([
        readinessService.dashboard(),
        readinessService.findings({ limit: 50 }),
        readinessService.checks({ limit: 50 }),
        readinessService.checklist(),
      ]);
      setDashboard(dash.data || null);
      setFindings(fnd.data || []);
      setChecks(chk.data || []);
      setChecklist(cl.data || []);
    } catch (err) { console.error(err); }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);
  useEffect(() => {
    if (!autoRefresh) return;
    const i = setInterval(fetchData, 15000);
    return () => clearInterval(i);
  }, [autoRefresh, fetchData]);

  const handleRunAutoChecks = async () => {
    try { await readinessService.runAutoChecks(); fetchData(); } catch (e) { console.error(e); }
  };

  const handleRunLoadTest = async () => {
    try { await readinessService.runLoadTest({ endpoint: '/api/v1/dashboard', concurrent_users: 10, duration_seconds: 5 }); fetchData(); } catch (e) { console.error(e); }
  };

  const handleFix = async (id) => {
    try { await readinessService.fixFinding(id, 'Fixed in Phase 49'); fetchData(); } catch (e) { console.error(e); }
  };

  const handleComplete = async (id) => {
    try { await readinessService.completeItem(id, 'Completed'); fetchData(); } catch (e) { console.error(e); }
  };

  const sevColor = { critical: '#EF4444', high: '#F97316', medium: '#FFA500', low: '#4F46E5', info: '#888' };
  const statusColor = { pass: '#22C55E', fail: '#EF4444', warning: '#FFA500', skip: '#888', manual: '#666' };
  const panel = { background: '#1A1A1E', borderRadius: '10px', border: '1px solid #333', padding: '14px' };
  const btn = { padding: '8px 16px', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '13px', color: '#fff' };

  return (
    <div style={{ padding: '24px' }}>
      <h1 style={{ fontSize: '28px', fontWeight: 700, marginBottom: '4px' }}>🚀 Production Readiness</h1>
      <p style={{ color: '#888', marginBottom: '12px' }}>Security audit, load testing, and deployment checklist</p>

      <div style={{ display: 'flex', gap: '4px', marginBottom: '12px', flexWrap: 'wrap' }}>
        {['overview', 'findings', 'checks', 'checklist'].map(t => (
          <button key={t} onClick={() => setTab(t)} style={{ ...btn, background: tab === t ? '#4F46E5' : '#1A1A1E', textTransform: 'capitalize' }}>{t}</button>
        ))}
        <button onClick={handleRunAutoChecks} style={{ ...btn, background: '#22C55E' }}>▶ Run Auto Checks</button>
        <button onClick={handleRunLoadTest} style={{ ...btn, background: '#F97316' }}>⚡ Load Test</button>
        <button onClick={() => setAutoRefresh(!autoRefresh)} style={{ ...btn, background: autoRefresh ? '#22C55E' : '#1A1A1E' }}>{autoRefresh ? '⏸ Auto' : '▶ Auto'}</button>
      </div>

      {tab === 'overview' && dashboard && (
        <div style={{ display: 'grid', gap: '12px' }}>
          {/* Readiness Score */}
          <div style={panel}>
            <div style={{ fontSize: '14px', fontWeight: 600, marginBottom: '8px' }}>Readiness Score</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
              <div style={{ fontSize: '48px', fontWeight: 700, color: dashboard.readiness_score?.overall_score >= 80 ? '#22C55E' : dashboard.readiness_score?.overall_score >= 60 ? '#FFA500' : '#EF4444' }}>
                {dashboard.readiness_score?.overall_score || 0}%
              </div>
              <div>
                <div style={{ fontSize: '16px', color: '#4F46E5' }}>{dashboard.readiness_score?.readiness_level?.replace('_', ' ')}</div>
                <div style={{ fontSize: '12px', color: '#888' }}>{dashboard.readiness_score?.passed || 0} passed · {dashboard.readiness_score?.warnings || 0} warnings · {dashboard.readiness_score?.failed || 0} failed · {dashboard.readiness_score?.manual || 0} manual</div>
              </div>
            </div>
            {/* Category scores */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(150px, 1fr))', gap: '6px', marginTop: '12px' }}>
              {Object.entries(dashboard.readiness_score?.category_scores || {}).map(([cat, score]) => (
                <div key={cat} style={{ padding: '6px', background: '#0D0D0F', borderRadius: '6px' }}>
                  <div style={{ fontSize: '10px', color: '#888', textTransform: 'capitalize' }}>{cat}</div>
                  <div style={{ fontSize: '14px', fontWeight: 600, color: score >= 80 ? '#22C55E' : score >= 60 ? '#FFA500' : '#EF4444' }}>{score}%</div>
                </div>
              ))}
            </div>
          </div>

          {/* Security & Checklist Stats */}
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            {[
              { l: 'Security Score', v: `${dashboard.security_scan?.security_score || 0}%`, c: dashboard.security_scan?.security_score >= 80 ? '#22C55E' : '#FFA500' },
              { l: 'Open Findings', v: dashboard.security_scan?.open_findings || 0, c: '#EF4444' },
              { l: 'Critical', v: dashboard.security_scan?.critical || 0, c: '#EF4444' },
              { l: 'High', v: dashboard.security_scan?.high || 0, c: '#F97316' },
              { l: 'Medium', v: dashboard.security_scan?.medium || 0, c: '#FFA500' },
              { l: 'Checklist', v: `${dashboard.checklist?.percentage || 0}%`, c: dashboard.checklist?.ready_to_deploy ? '#22C55E' : '#FFA500' },
              { l: 'Required Done', v: `${dashboard.checklist?.required_completed || 0}/${dashboard.checklist?.required_total || 0}`, c: '#4F46E5' },
              { l: 'Ready to Deploy', v: dashboard.checklist?.ready_to_deploy ? '✅' : '❌', c: dashboard.checklist?.ready_to_deploy ? '#22C55E' : '#EF4444' },
            ].map(s => (
              <div key={s.l} style={{ ...panel, flex: '1 1 100px', textAlign: 'center' }}>
                <div style={{ fontSize: '10px', color: '#888' }}>{s.l}</div>
                <div style={{ fontSize: '16px', fontWeight: 700, color: s.c || '#fff' }}>{s.v}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {tab === 'findings' && (
        <div style={{ display: 'grid', gap: '6px' }}>
          {findings.map((f, i) => (
            <div key={i} style={{ ...panel, borderLeft: `3px solid ${sevColor[f.severity] || '#888'}` }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <div style={{ fontSize: '13px', fontWeight: 600 }}>{f.title}</div>
                <div style={{ display: 'flex', gap: '4px' }}>
                  <span style={{ fontSize: '9px', padding: '2px 6px', borderRadius: '4px', background: (sevColor[f.severity] || '#888') + '22', color: sevColor[f.severity] || '#888' }}>{f.severity}</span>
                  <span style={{ fontSize: '9px', padding: '2px 6px', borderRadius: '4px', background: f.status === 'open' ? '#EF444422' : '#22C55E22', color: f.status === 'open' ? '#EF4444' : '#22C55E' }}>{f.status}</span>
                  {f.status === 'open' && <button onClick={() => handleFix(f.id)} style={{ ...btn, background: '#22C55E', fontSize: '10px', padding: '2px 8px' }}>Fix</button>}
                </div>
              </div>
              <div style={{ fontSize: '11px', color: '#888', marginTop: '4px' }}>{f.description}</div>
              <div style={{ fontSize: '10px', color: '#666', marginTop: '4px' }}>
                📁 {f.location} | {f.cwe && `CWE: ${f.cwe} | `}Recommendation: {f.recommendation}
              </div>
            </div>
          ))}
        </div>
      )}

      {tab === 'checks' && (
        <div style={{ display: 'grid', gap: '4px' }}>
          {checks.map((c, i) => (
            <div key={i} style={panel}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <div style={{ fontSize: '13px', fontWeight: 600 }}>{c.name}</div>
                <span style={{ fontSize: '9px', padding: '2px 6px', borderRadius: '4px', background: (statusColor[c.status] || '#666') + '22', color: statusColor[c.status] || '#666' }}>{c.status}</span>
              </div>
              <div style={{ fontSize: '11px', color: '#888', marginTop: '4px' }}>
                {c.description} | Category: <b>{c.category}</b> | Weight: {c.weight} | Auto: {c.auto_check ? '✓' : '✗'}
              </div>
            </div>
          ))}
        </div>
      )}

      {tab === 'checklist' && (
        <div style={{ display: 'grid', gap: '4px' }}>
          {checklist.map((item, i) => (
            <div key={i} style={{ ...panel, opacity: item.completed ? 0.6 : 1 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                  <span style={{ fontSize: '14px' }}>{item.completed ? '✅' : '⬜'}</span>
                  <div>
                    <div style={{ fontSize: '13px', fontWeight: item.completed ? '400' : '600' }}>{item.item}</div>
                    <div style={{ fontSize: '10px', color: '#888' }}>{item.category}{item.required ? ' · required' : ' · optional'}</div>
                  </div>
                </div>
                {!item.completed && (
                  <button onClick={() => handleComplete(item.id)} style={{ ...btn, background: '#4F46E5', fontSize: '10px', padding: '4px 10px' }}>Complete</button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default ProductionReadiness;
