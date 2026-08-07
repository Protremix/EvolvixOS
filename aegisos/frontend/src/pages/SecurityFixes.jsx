import React, { useState, useEffect, useCallback } from 'react';
import securityService from '../services/securityService';

function SecurityFixes() {
  const [summary, setSummary] = useState(null);
  const [breakers, setBreakers] = useState([]);
  const [jwtConfig, setJwtConfig] = useState(null);
  const [rateLimit, setRateLimit] = useState(null);
  const [secretMgr, setSecretMgr] = useState(null);

  const fetchData = useCallback(async () => {
    try {
      const [sum, cb, jwt, rl, sm] = await Promise.all([
        securityService.summary(),
        securityService.circuitBreakers(),
        securityService.jwtConfig(),
        securityService.authRateLimitStats(),
        securityService.secretManagerConfig(),
      ]);
      setSummary(sum.data || null);
      setBreakers(cb.data || []);
      setJwtConfig(jwt.data || null);
      setRateLimit(rl.data || null);
      setSecretMgr(sm.data || null);
    } catch (err) { console.error(err); }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const panel = { background: '#1A1A1E', borderRadius: '10px', border: '1px solid #333', padding: '14px' };
  const stateColor = { closed: '#22C55E', open: '#EF4444', half_open: '#FFA500' };

  return (
    <div style={{ padding: '24px' }}>
      <h1 style={{ fontSize: '28px', fontWeight: 700, marginBottom: '4px' }}>🔐 Security Fixes</h1>
      <p style={{ color: '#888', marginBottom: '12px' }}>Phase 50 — All high and medium security findings resolved</p>

      {/* Summary */}
      {summary && (
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '12px' }}>
          {[
            { l: 'Total Fixes', v: summary.total_fixes, c: '#4F46E5' },
            { l: 'High Fixed', v: summary.high_fixed, c: '#F97316' },
            { l: 'Medium Fixed', v: summary.medium_fixed, c: '#22C55E' },
            { l: 'Remaining Open', v: summary.remaining_open, c: '#FFA500' },
          ].map(s => (
            <div key={s.l} style={{ ...panel, flex: '1 1 100px', textAlign: 'center' }}>
              <div style={{ fontSize: '10px', color: '#888' }}>{s.l}</div>
              <div style={{ fontSize: '20px', fontWeight: 700, color: s.c }}>{s.v}</div>
            </div>
          ))}
        </div>
      )}

      {/* Fixes */}
      {summary?.fixes?.map((fix, i) => (
        <div key={i} style={{ ...panel, marginBottom: '8px', borderLeft: `3px solid ${fix.severity === 'high' ? '#F97316' : '#22C55E'}` }}>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <div style={{ fontSize: '13px', fontWeight: 600 }}>{fix.title}</div>
            <span style={{ fontSize: '9px', padding: '2px 6px', borderRadius: '4px', background: '#22C55E22', color: '#22C55E' }}>✓ {fix.status}</span>
          </div>
          <div style={{ fontSize: '11px', color: '#888', marginTop: '4px' }}>{fix.description}</div>
          <div style={{ fontSize: '10px', color: '#666', marginTop: '2px' }}>📁 {fix.file} | {fix.details}</div>
        </div>
      ))}

      {/* Circuit Breakers */}
      <div style={panel}>
        <div style={{ fontSize: '14px', fontWeight: 600, marginBottom: '8px' }}>Circuit Breakers</div>
        {breakers.map((b, i) => (
          <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', borderBottom: '1px solid #222', fontSize: '12px' }}>
            <span>{b.name}</span>
            <div style={{ display: 'flex', gap: '8px' }}>
              <span style={{ color: stateColor[b.state] || '#888' }}>● {b.state}</span>
              <span style={{ color: '#888' }}>Failures: {b.failure_count}</span>
              <span style={{ color: '#888' }}>Total: {b.stats?.total_calls || 0}</span>
            </div>
          </div>
        ))}
      </div>

      {/* JWT Config */}
      {jwtConfig && (
        <div style={{ ...panel, marginTop: '8px' }}>
          <div style={{ fontSize: '14px', fontWeight: 600, marginBottom: '8px' }}>JWT Configuration</div>
          <div style={{ fontSize: '12px', color: '#888' }}>
            <div>Access Token: <b style={{ color: '#4F46E5' }}>{jwtConfig.access_token_expiry_hours}h</b> (was {jwtConfig.previous_expiry_hours}h)</div>
            <div>Refresh Token: <b style={{ color: '#4F46E5' }}>{jwtConfig.refresh_token_expiry_days}d</b></div>
            <div style={{ fontSize: '10px', color: '#22C55E', marginTop: '4px' }}>{jwtConfig.improvement}</div>
          </div>
        </div>
      )}

      {/* Rate Limit */}
      {rateLimit && (
        <div style={{ ...panel, marginTop: '8px' }}>
          <div style={{ fontSize: '14px', fontWeight: 600, marginBottom: '8px' }}>Auth Rate Limiting</div>
          <div style={{ fontSize: '12px', color: '#888' }}>
            <div>IP Limit: <b style={{ color: '#4F46E5' }}>{rateLimit.ip_limit_per_minute}/min</b></div>
            <div>Address Limit: <b style={{ color: '#4F46E5' }}>{rateLimit.address_limit_per_hour}/hr</b></div>
            <div>Lockout: <b style={{ color: '#4F46E5' }}>{rateLimit.lockout_duration}s</b></div>
          </div>
        </div>
      )}

      {/* Secret Manager */}
      {secretMgr && (
        <div style={{ ...panel, marginTop: '8px' }}>
          <div style={{ fontSize: '14px', fontWeight: 600, marginBottom: '8px' }}>Secret Manager</div>
          <div style={{ fontSize: '12px', color: '#888' }}>{secretMgr.message}</div>
        </div>
      )}
    </div>
  );
}

export default SecurityFixes;
