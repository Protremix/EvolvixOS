import React, { useState, useEffect, useCallback } from 'react';
import enhancedSecurityService from '../services/enhancedSecurityService';

function EnhancedSecurity() {
  const [tab, setTab] = useState('audit');
  const [dashboard, setDashboard] = useState(null);
  const [audit, setAudit] = useState([]);
  const [auditSummary, setAuditSummary] = useState(null);
  const [threats, setThreats] = useState([]);
  const [threatStats, setThreatStats] = useState(null);
  const [encryption, setEncryption] = useState([]);
  const [monitoring, setMonitoring] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const [dash, aud, sum, thr, tstats, enc] = await Promise.all([
        enhancedSecurityService.dashboard(),
        enhancedSecurityService.audit({ limit: 100 }),
        enhancedSecurityService.auditSummary(),
        enhancedSecurityService.threats({ limit: 50 }),
        enhancedSecurityService.threatStats(),
        enhancedSecurityService.encryption(),
      ]);
      setDashboard(dash.data || null);
      setAudit(aud.data || []);
      setAuditSummary(sum.data || null);
      setThreats(thr.data || []);
      setThreatStats(tstats.data || null);
      setEncryption(enc.data || []);
      setMonitoring(dash.data?.monitoring || false);
    } catch (err) { console.error(err); }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleMonitoring = async () => {
    try {
      if (monitoring) await enhancedSecurityService.stopMonitoring();
      else await enhancedSecurityService.startMonitoring();
      setMonitoring(!monitoring);
    } catch (e) { console.error(e); }
  };

  const panel = { background: '#1A1A1E', borderRadius: '10px', border: '1px solid #333', padding: '14px' };
  const btn = { padding: '6px 12px', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '12px', color: '#fff' };
  const sevColor = { critical: '#EF4444', high: '#F97316', medium: '#FFA500', low: '#4F46E5', info: '#888' };
  const statusColor = { pass: '#22C55E', fail: '#EF4444', warning: '#FFA500', skip: '#888' };
  const threatColor = { info: '#3B82F6', low: '#4F46E5', medium: '#FFA500', high: '#F97316', critical: '#EF4444' };

  return (
    <div style={{ padding: '24px' }}>
      <h1 style={{ fontSize: '28px', fontWeight: 700, marginBottom: '4px' }}>🛡️ Enhanced Security</h1>
      <p style={{ color: '#888', marginBottom: '12px' }}>Security audit, threat monitoring, ZKP, MFA, encryption</p>

      {auditSummary && (
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '12px' }}>
          {[
            { l: 'Security Score', v: `${auditSummary.security_score}%`, c: auditSummary.security_score >= 90 ? '#22C55E' : auditSummary.security_score >= 80 ? '#FFA500' : '#F97316' },
            { l: 'Grade', v: auditSummary.grade, c: '#4F46E5' },
            { l: 'Pass', v: auditSummary.pass_count, c: '#22C55E' },
            { l: 'Warnings', v: auditSummary.warning_count, c: '#FFA500' },
            { l: 'Fail', v: auditSummary.fail_count, c: '#EF4444' },
            { l: 'Blocked IPs', v: dashboard?.blocked_ips || 0, c: '#EF4444' },
            { l: 'MFA Users', v: dashboard?.mfa_count || 0, c: '#A855F7' },
            { l: 'ZKP Proofs', v: dashboard?.zkp_count || 0, c: '#06B6D4' },
          ].map(s => (
            <div key={s.l} style={{ ...panel, flex: '1 1 80px', textAlign: 'center' }}>
              <div style={{ fontSize: '10px', color: '#888' }}>{s.l}</div>
              <div style={{ fontSize: '16px', fontWeight: 700, color: s.c }}>{s.v}</div>
            </div>
          ))}
        </div>
      )}

      {auditSummary && auditSummary.warning_count === 0 && (
        <div style={{ ...panel, borderLeft: '3px solid #22C55E', marginBottom: '12px' }}>
          <div style={{ fontSize: '14px', fontWeight: 600, color: '#22C55E' }}>✅ All Security Findings Resolved</div>
          <div style={{ fontSize: '12px', color: '#888', marginTop: '4px' }}>
            Phase 55: CSP headers, CSRF protection, CORS hardening, error sanitization, and security headers all implemented.
          </div>
        </div>
      )}

      <div style={{ display: 'flex', gap: '4px', marginBottom: '12px', flexWrap: 'wrap', alignItems: 'center' }}>
        {['audit', 'threats', 'encryption'].map(t => (
          <button key={t} onClick={() => setTab(t)} style={{ ...btn, background: tab === t ? '#4F46E5' : '#1A1A1E', textTransform: 'capitalize' }}>{t}</button>
        ))}
        <button onClick={handleMonitoring} style={{ ...btn, background: monitoring ? '#22C55E' : '#1A1A1E' }}>
          {monitoring ? '● Monitoring Active' : '○ Monitoring Off'}
        </button>
      </div>

      {tab === 'audit' && (
        <div style={{ display: 'grid', gap: '4px' }}>
          {audit.map((item, i) => (
            <div key={i} style={{ ...panel, borderLeft: `3px solid ${sevColor[item.severity] || '#888'}` }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <div style={{ fontSize: '13px', fontWeight: 600 }}>{item.title}</div>
                <div style={{ display: 'flex', gap: '4px' }}>
                  <span style={{ fontSize: '9px', padding: '2px 6px', borderRadius: '4px', background: (statusColor[item.status] || '#888') + '22', color: statusColor[item.status] || '#888' }}>{item.status}</span>
                  <span style={{ fontSize: '9px', padding: '2px 6px', borderRadius: '4px', background: (sevColor[item.severity] || '#888') + '22', color: sevColor[item.severity] || '#888' }}>{item.severity}</span>
                </div>
              </div>
              <div style={{ fontSize: '11px', color: '#888', marginTop: '4px' }}>{item.description}</div>
              <div style={{ fontSize: '10px', color: '#666', marginTop: '4px' }}>
                Category: {item.category} | CWE: {item.cwe || 'N/A'}
                {item.evidence && ` | Evidence: ${item.evidence}`}
              </div>
            </div>
          ))}
        </div>
      )}

      {tab === 'threats' && (
        <div style={{ display: 'grid', gap: '4px' }}>
          {threats.map((t, i) => (
            <div key={i} style={{ ...panel, borderLeft: `3px solid ${threatColor[t.level] || '#888'}` }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <div style={{ fontSize: '13px', fontWeight: 600 }}>{t.type.replace(/_/g, ' ')}</div>
                <div style={{ display: 'flex', gap: '4px' }}>
                  <span style={{ fontSize: '9px', padding: '2px 6px', borderRadius: '4px', background: (threatColor[t.level] || '#888') + '22', color: threatColor[t.level] || '#888' }}>{t.level}</span>
                  <span style={{ fontSize: '9px', padding: '2px 6px', borderRadius: '4px', background: '#222', color: '#888' }}>{t.status}</span>
                </div>
              </div>
              <div style={{ fontSize: '11px', color: '#888', marginTop: '4px' }}>{t.description}</div>
              <div style={{ fontSize: '10px', color: '#666', marginTop: '4px' }}>
                IP: {t.source_ip || 'N/A'} | Target: {t.target || 'N/A'}
                {t.mitigation && ` | Mitigation: ${t.mitigation}`}
              </div>
            </div>
          ))}
        </div>
      )}

      {tab === 'encryption' && (
        <div style={{ display: 'grid', gap: '4px' }}>
          {encryption.map((c, i) => (
            <div key={i} style={panel}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <div style={{ fontSize: '13px', fontWeight: 600 }}>🔒 {c.component}</div>
                <span style={{ fontSize: '9px', padding: '2px 6px', borderRadius: '4px', background: '#22C55E22', color: '#22C55E' }}>{c.status}</span>
              </div>
              <div style={{ fontSize: '11px', color: '#888', marginTop: '4px' }}>Algorithm: {c.algorithm} | Key: {c.key_size}-bit</div>
              <div style={{ fontSize: '10px', color: '#666', marginTop: '4px' }}>
                Last rotated: {new Date(c.last_rotated).toLocaleDateString()}
                {c.next_rotation && ` | Next: ${new Date(c.next_rotation).toLocaleDateString()}`}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default EnhancedSecurity;
