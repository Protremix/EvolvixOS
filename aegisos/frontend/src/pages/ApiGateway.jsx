import React, { useState, useEffect, useCallback } from 'react';
import gatewayService from '../services/gatewayService';

function ApiGateway() {
  const [tab, setTab] = useState('overview');
  const [dashboard, setDashboard] = useState(null);
  const [keys, setKeys] = useState([]);
  const [routes, setRoutes] = useState([]);
  const [newKeyName, setNewKeyName] = useState('');
  const [createdKey, setCreatedKey] = useState(null);
  const [autoRefresh, setAutoRefresh] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const [dash, ks, rs] = await Promise.all([
        gatewayService.dashboard(),
        gatewayService.keys(),
        gatewayService.routes(),
      ]);
      setDashboard(dash.data || null);
      setKeys(ks.data || []);
      setRoutes(rs.data || []);
    } catch (err) { console.error(err); }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);
  useEffect(() => {
    if (!autoRefresh) return;
    const i = setInterval(fetchData, 10000);
    return () => clearInterval(i);
  }, [autoRefresh, fetchData]);

  const handleCreateKey = async () => {
    if (!newKeyName) return;
    try {
      const r = await gatewayService.createKey({ name: newKeyName, scopes: ['*'], rate_limit: 1000 });
      setCreatedKey(r.data);
      setNewKeyName('');
      fetchData();
    } catch (e) { console.error(e); }
  };

  const handleRevoke = async (id) => {
    try { await gatewayService.revokeKey(id); fetchData(); } catch (e) { console.error(e); }
  };

  const statusColor = { active: '#22C55E', revoked: '#EF4444', expired: '#888', disabled: '#888', maintenance: '#FFA500' };
  const circuitColor = { closed: '#22C55E', open: '#EF4444', half_open: '#FFA500' };
  const panel = { background: '#1A1A1E', borderRadius: '10px', border: '1px solid #333', padding: '14px' };
  const btn = { padding: '8px 16px', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '13px', color: '#fff' };
  const input = { padding: '8px 12px', background: '#0D0D0F', border: '1px solid #333', borderRadius: '6px', color: '#fff', fontSize: '13px', width: '100%' };

  return (
    <div style={{ padding: '24px' }}>
      <h1 style={{ fontSize: '28px', fontWeight: 700, marginBottom: '4px' }}>🚪 API Gateway</h1>
      <p style={{ color: '#888', marginBottom: '12px' }}>Routing, rate limiting, caching, and monitoring</p>

      <div style={{ display: 'flex', gap: '4px', marginBottom: '12px' }}>
        {['overview', 'keys', 'routes', 'circuits'].map(t => (
          <button key={t} onClick={() => setTab(t)} style={{ ...btn, background: tab === t ? '#4F46E5' : '#1A1A1E', textTransform: 'capitalize' }}>{t}</button>
        ))}
        <button onClick={() => setAutoRefresh(!autoRefresh)} style={{ ...btn, background: autoRefresh ? '#22C55E' : '#1A1A1E' }}>{autoRefresh ? '⏸ Auto' : '▶ Auto'}</button>
      </div>

      {tab === 'overview' && dashboard && (
        <div style={{ display: 'grid', gap: '12px' }}>
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            {[
              { l: 'API Keys', v: `${dashboard.keys?.active || 0}/${dashboard.keys?.total || 0}` },
              { l: 'Routes', v: `${dashboard.routes?.active || 0}/${dashboard.routes?.total || 0}` },
              { l: 'Cache Entries', v: dashboard.cache?.cached_entries || 0 },
              { l: 'Cache Hits', v: dashboard.cache?.total_hits || 0 },
              { l: 'Requests (24h)', v: dashboard.usage_24h?.total_requests || 0 },
              { l: 'Avg Latency', v: `${dashboard.usage_24h?.avg_latency_ms || 0}ms` },
              { l: 'Cache Hit Rate', v: `${(dashboard.usage_24h?.cache_hit_rate || 0) * 100}%` },
              { l: 'Services', v: dashboard.services?.length || 0 },
            ].map(s => (
              <div key={s.l} style={{ ...panel, flex: '1 1 100px', textAlign: 'center' }}>
                <div style={{ fontSize: '10px', color: '#888' }}>{s.l}</div>
                <div style={{ fontSize: '16px', fontWeight: 700 }}>{s.v}</div>
              </div>
            ))}
          </div>

          {/* Service Health */}
          <div style={panel}>
            <div style={{ fontSize: '14px', fontWeight: 600, marginBottom: '8px' }}>Service Health</div>
            {dashboard.services?.map((s, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', borderBottom: '1px solid #222', fontSize: '12px' }}>
                <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                  <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: s.healthy ? '#22C55E' : '#EF4444' }} />
                  <span>{s.service}</span>
                </div>
                <div style={{ display: 'flex', gap: '12px', fontSize: '10px', color: '#888' }}>
                  <span>Requests: {s.total_requests}</span>
                  <span>Errors: {s.error_count}</span>
                  <span>Latency: {s.avg_latency_ms}ms</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {tab === 'keys' && (
        <div style={{ display: 'grid', gap: '12px' }}>
          <div style={{ ...panel, maxWidth: '500px' }}>
            <div style={{ fontSize: '14px', fontWeight: 600, marginBottom: '12px' }}>Create API Key</div>
            <div style={{ display: 'flex', gap: '8px' }}>
              <input value={newKeyName} onChange={e => setNewKeyName(e.target.value)} placeholder="Key name" style={input} />
              <button onClick={handleCreateKey} style={{ ...btn, background: '#4F46E5' }}>Create</button>
            </div>
            {createdKey && (
              <div style={{ marginTop: '12px', padding: '8px', background: '#0D0D0F', borderRadius: '6px', fontSize: '11px' }}>
                <div style={{ color: '#22C55E', marginBottom: '4px' }}>Key created! Save this — it won't be shown again:</div>
                <code style={{ color: '#4F46E5', wordBreak: 'break-all' }}>{createdKey.api_key}</code>
              </div>
            )}
          </div>

          {keys.map((k, i) => (
            <div key={i} style={panel}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <div style={{ fontSize: '13px', fontWeight: 600 }}>{k.name}</div>
                <span style={{ fontSize: '9px', padding: '2px 6px', borderRadius: '4px', background: (statusColor[k.status] || '#888') + '22', color: statusColor[k.status] || '#888' }}>{k.status}</span>
              </div>
              <div style={{ display: 'flex', gap: '12px', fontSize: '11px', marginTop: '4px', color: '#888', flexWrap: 'wrap' }}>
                <span>ID: {k.key_id}</span>
                <span>Scopes: {k.scopes?.join(', ')}</span>
                <span>Rate: {k.rate_limit}/min</span>
                <span>Requests: {k.total_requests}</span>
                {k.last_used && <span>Last used: {new Date(k.last_used).toLocaleString()}</span>}
              </div>
              {k.status === 'active' && (
                <button onClick={() => handleRevoke(k.key_id)} style={{ ...btn, background: '#EF4444', fontSize: '11px', padding: '4px 12px', marginTop: '8px' }}>Revoke</button>
              )}
            </div>
          ))}
        </div>
      )}

      {tab === 'routes' && (
        <div style={{ display: 'grid', gap: '6px' }}>
          {routes.map((r, i) => (
            <div key={i} style={panel}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <div style={{ fontSize: '13px', fontWeight: 600 }}>{r.path}</div>
                <span style={{ fontSize: '9px', padding: '2px 6px', borderRadius: '4px', background: (statusColor[r.status] || '#888') + '22', color: statusColor[r.status] || '#888' }}>{r.status}</span>
              </div>
              <div style={{ display: 'flex', gap: '12px', fontSize: '11px', marginTop: '4px', color: '#888', flexWrap: 'wrap' }}>
                <span>Target: <b style={{ color: '#4F46E5' }}>{r.target_service}</b></span>
                <span>Methods: {r.methods?.join(', ')}</span>
                <span>Cache: {r.cache_ttl > 0 ? `${r.cache_ttl}s` : 'off'}</span>
                <span>Auth: {r.auth_required ? 'required' : 'open'}</span>
                <span>Requests: {r.request_count}</span>
                <span>Avg latency: {r.avg_latency_ms}ms</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {tab === 'circuits' && dashboard && (
        <div style={{ display: 'grid', gap: '6px' }}>
          {dashboard.circuits?.map((c, i) => (
            <div key={i} style={panel}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <div style={{ fontSize: '13px' }}>{c.route_id}</div>
                <span style={{ fontSize: '9px', padding: '2px 6px', borderRadius: '4px', background: (circuitColor[c.state] || '#888') + '22', color: circuitColor[c.state] || '#888' }}>{c.state}</span>
              </div>
              <div style={{ fontSize: '11px', color: '#888', marginTop: '4px' }}>Failures: {c.failures}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default ApiGateway;
