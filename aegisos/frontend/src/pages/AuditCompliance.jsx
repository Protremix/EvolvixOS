import React, { useState, useEffect, useCallback } from 'react';
import auditService from '../services/auditService';

function AuditCompliance() {
  const [tab, setTab] = useState('overview');
  const [dashboard, setDashboard] = useState(null);
  const [audit, setAudit] = useState([]);
  const [checks, setChecks] = useState([]);
  const [reports, setReports] = useState([]);
  const [policies, setPolicies] = useState([]);
  const [risks, setRisks] = useState([]);
  const [autoRefresh, setAutoRefresh] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const [dash, aud, chk, pol, rsk] = await Promise.all([
        auditService.dashboard(),
        auditService.audit({ limit: 50 }),
        auditService.checks(),
        auditService.policies(),
        auditService.risks(),
      ]);
      setDashboard(dash.data || null);
      setAudit(aud.data || []);
      setChecks(chk.data || []);
      setPolicies(pol.data || []);
      setRisks(rsk.data || []);
    } catch (err) { console.error(err); }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);
  useEffect(() => {
    if (!autoRefresh) return;
    const i = setInterval(fetchData, 10000);
    return () => clearInterval(i);
  }, [autoRefresh, fetchData]);

  const handleGenerateReport = async (framework) => {
    try { await auditService.generateReport({ framework, title: `${framework.toUpperCase()} Report ${new Date().toISOString().slice(0,10)}` }); fetchData(); } catch (e) { console.error(e); }
  };

  const handleRunCheck = async (id) => {
    try { await auditService.runCheck(id); fetchData(); } catch (e) { console.error(e); }
  };

  const sevColor = { info: '#4F46E5', warning: '#FFA500', error: '#EF4444', critical: '#EF4444' };
  const statusColor = { compliant: '#22C55E', non_compliant: '#EF4444', partially_compliant: '#FFA500', pending_review: '#888', not_applicable: '#666' };
  const riskColor = { low: '#22C55E', medium: '#FFA500', high: '#EF4444', critical: '#EF4444' };
  const panel = { background: '#1A1A1E', borderRadius: '10px', border: '1px solid #333', padding: '14px' };
  const btn = { padding: '8px 16px', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '13px', color: '#fff' };

  return (
    <div style={{ padding: '24px' }}>
      <h1 style={{ fontSize: '28px', fontWeight: 700, marginBottom: '4px' }}>📋 Audit & Compliance</h1>
      <p style={{ color: '#888', marginBottom: '12px' }}>Audit trails, compliance frameworks, and risk management</p>

      <div style={{ display: 'flex', gap: '4px', marginBottom: '12px', flexWrap: 'wrap' }}>
        {['overview', 'audit', 'checks', 'policies', 'risks'].map(t => (
          <button key={t} onClick={() => setTab(t)} style={{ ...btn, background: tab === t ? '#4F46E5' : '#1A1A1E', textTransform: 'capitalize' }}>{t}</button>
        ))}
        <button onClick={() => setAutoRefresh(!autoRefresh)} style={{ ...btn, background: autoRefresh ? '#22C55E' : '#1A1A1E' }}>{autoRefresh ? '⏸ Auto' : '▶ Auto'}</button>
      </div>

      {tab === 'overview' && dashboard && (
        <div style={{ display: 'grid', gap: '12px' }}>
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            {[
              { l: 'Audit Entries', v: dashboard.total_audit_entries },
              { l: 'Checks (24h)', v: dashboard.audit_stats_24h?.total_entries || 0 },
              { l: 'Policies', v: dashboard.total_policies },
              { l: 'Open Risks', v: dashboard.open_risks },
              { l: 'Critical Risks', v: dashboard.critical_risks },
              { l: 'Reports', v: dashboard.total_reports },
            ].map(s => (
              <div key={s.l} style={{ ...panel, flex: '1 1 100px', textAlign: 'center' }}>
                <div style={{ fontSize: '10px', color: '#888' }}>{s.l}</div>
                <div style={{ fontSize: '16px', fontWeight: 700 }}>{s.v}</div>
              </div>
            ))}
          </div>

          {/* Framework Summary */}
          <div style={panel}>
            <div style={{ fontSize: '14px', fontWeight: 600, marginBottom: '8px' }}>Framework Compliance</div>
            {Object.entries(dashboard.frameworks || {}).map(([fw, data]) => (
              <div key={fw} style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', borderBottom: '1px solid #222', fontSize: '12px' }}>
                <span style={{ textTransform: 'uppercase' }}>{fw.replace('_', '/')}</span>
                <div style={{ display: 'flex', gap: '12px' }}>
                  <span style={{ color: '#888' }}>{data.compliant}/{data.total}</span>
                  <span style={{ color: data.score >= 80 ? '#22C55E' : data.score >= 60 ? '#FFA500' : '#EF4444' }}>{data.score}%</span>
                  <button onClick={() => handleGenerateReport(fw)} style={{ ...btn, background: '#4F46E5', fontSize: '10px', padding: '2px 8px' }}>Report</button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {tab === 'audit' && (
        <div style={{ display: 'grid', gap: '4px' }}>
          {audit.slice(0, 30).map((e, i) => (
            <div key={i} style={{ ...panel, borderLeft: `3px solid ${sevColor[e.severity] || '#888'}` }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <div style={{ fontSize: '12px', fontWeight: 600 }}>{e.action}</div>
                <span style={{ fontSize: '9px', padding: '2px 6px', borderRadius: '4px', background: (sevColor[e.severity] || '#888') + '22', color: sevColor[e.severity] || '#888' }}>{e.severity}</span>
              </div>
              <div style={{ display: 'flex', gap: '12px', fontSize: '10px', marginTop: '4px', color: '#888', flexWrap: 'wrap' }}>
                <span>Category: {e.category}</span>
                <span>Actor: {e.actor}</span>
                <span>Resource: {e.resource}</span>
                <span style={{ color: e.result === 'success' ? '#22C55E' : '#EF4444' }}>{e.result}</span>
                <span>{new Date(e.timestamp).toLocaleString()}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {tab === 'checks' && (
        <div style={{ display: 'grid', gap: '6px' }}>
          {checks.map((c, i) => (
            <div key={i} style={panel}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <div style={{ fontSize: '12px', fontWeight: 600 }}>{c.control_id}: {c.title}</div>
                <div style={{ display: 'flex', gap: '4px' }}>
                  <span style={{ fontSize: '9px', padding: '2px 6px', borderRadius: '4px', background: (statusColor[c.status] || '#888') + '22', color: statusColor[c.status] || '#888' }}>{c.status.replace(/_/g, ' ')}</span>
                  <button onClick={() => handleRunCheck(c.id)} style={{ ...btn, background: '#4F46E5', fontSize: '10px', padding: '2px 8px' }}>Run</button>
                </div>
              </div>
              <div style={{ fontSize: '10px', color: '#888', marginTop: '4px' }}>
                {c.description} | Framework: {c.framework.toUpperCase()} | Pass: {c.pass_count}/{c.check_count} | Risk: <span style={{ color: riskColor[c.risk_level] }}>{c.risk_level}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {tab === 'policies' && (
        <div style={{ display: 'grid', gap: '6px' }}>
          {policies.map((p, i) => (
            <div key={i} style={panel}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <div style={{ fontSize: '12px', fontWeight: 600 }}>{p.name}</div>
                <span style={{ fontSize: '9px', padding: '2px 6px', borderRadius: '4px', background: p.enabled ? '#22C55E22' : '#EF444422', color: p.enabled ? '#22C55E' : '#EF4444' }}>{p.enabled ? 'enabled' : 'disabled'}</span>
              </div>
              <div style={{ fontSize: '10px', color: '#888', marginTop: '4px' }}>
                {p.description} | Framework: {p.framework.toUpperCase()} | Type: {p.rule_type} | Violations: {p.violations}
              </div>
            </div>
          ))}
        </div>
      )}

      {tab === 'risks' && (
        <div style={{ display: 'grid', gap: '6px' }}>
          {risks.map((r, i) => (
            <div key={i} style={{ ...panel, borderLeft: `3px solid ${riskColor[r.risk_level] || '#888'}` }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <div style={{ fontSize: '12px', fontWeight: 600 }}>{r.title}</div>
                <span style={{ fontSize: '9px', padding: '2px 6px', borderRadius: '4px', background: (riskColor[r.risk_level] || '#888') + '22', color: riskColor[r.risk_level] || '#888' }}>{r.risk_level}</span>
              </div>
              <div style={{ fontSize: '10px', color: '#888', marginTop: '4px' }}>
                {r.description} | Score: {r.risk_score} | P: {r.probability} × I: {r.impact} | Status: {r.status}
              </div>
            </div>
          ))}
          {risks.length === 0 && <div style={{ fontSize: '12px', color: '#888', textAlign: 'center', padding: '20px' }}>No risks registered</div>}
        </div>
      )}
    </div>
  );
}

export default AuditCompliance;
