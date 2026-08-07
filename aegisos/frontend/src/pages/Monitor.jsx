import React, { useState, useEffect, useCallback } from 'react';
import monitorService from '../services/monitorService';

function Monitor() {
  const [health, setHealth] = useState(null);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const fetchHealth = useCallback(async () => {
    try {
      const resp = await monitorService.health();
      setHealth(resp.data);
    } catch (err) { console.error(err); }
  }, []);

  useEffect(() => {
    fetchHealth();
    if (autoRefresh) {
      const interval = setInterval(fetchHealth, 5000);
      return () => clearInterval(interval);
    }
  }, [fetchHealth, autoRefresh]);

  const panel = { background: '#1A1A1E', borderRadius: '10px', border: '1px solid #333', padding: '14px' };
  const statusColor = { healthy: '#22C55E', degraded: '#FFA500', offline: '#EF4444' };

  return (
    <div style={{ padding: '24px' }}>
      <h1 style={{ fontSize: '28px', fontWeight: 700, marginBottom: '4px' }}>📊 Local Monitor</h1>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <p style={{ color: '#888' }}>Service health & system metrics</p>
        <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: '#888' }}>
          <input type="checkbox" checked={autoRefresh} onChange={e => setAutoRefresh(e.target.checked)} /> Auto-refresh
        </label>
      </div>

      {health && (
        <>
          {/* Overall status */}
          <div style={{ ...panel, marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: statusColor[health.summary.overall] }} />
            <span style={{ fontSize: '14px', fontWeight: 600, color: statusColor[health.summary.overall] }}>
              {health.summary.overall.toUpperCase()}
            </span>
            <span style={{ fontSize: '12px', color: '#888' }}>
              {health.summary.healthy}/{health.summary.total} services healthy
            </span>
          </div>

          {/* Services */}
          <div style={{ display: 'grid', gap: '6px', marginBottom: '12px' }}>
            {health.services?.map((s, i) => (
              <div key={i} style={{ ...panel, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <div style={{ fontSize: '13px', fontWeight: 600 }}>{s.name}</div>
                  <div style={{ fontSize: '10px', color: '#888' }}>{s.url}</div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <span style={{ fontSize: '11px', padding: '2px 8px', borderRadius: '4px', background: (statusColor[s.status] || '#888') + '22', color: statusColor[s.status] || '#888', fontWeight: 600 }}>
                    {s.status}
                  </span>
                  {s.response_time_ms > 0 && (
                    <div style={{ fontSize: '10px', color: '#888' }}>{s.response_time_ms}ms</div>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* System metrics */}
          {health.system && !health.system.error && (
            <>
              <div style={{ fontSize: '14px', fontWeight: 600, color: '#4F46E5', marginBottom: '8px' }}>System</div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(120px, 1fr))', gap: '8px' }}>
                <Metric label="CPU" value={`${health.system.cpu_percent}%`} color="#4F46E5" />
                <Metric label="Memory" value={`${health.system.memory_percent}%`} sub={`${health.system.memory_used_gb}/${health.system.memory_total_gb}GB`} color="#22C55E" />
                <Metric label="Disk" value={`${health.system.disk_percent}%`} sub={`${health.system.disk_used_gb}/${health.system.disk_total_gb}GB`} color="#FFA500" />
              </div>
            </>
          )}
        </>
      )}
    </div>
  );
}

function Metric({ label, value, sub, color }) {
  return (
    <div style={{ background: '#1A1A1E', borderRadius: '8px', padding: '12px', border: '1px solid #333' }}>
      <div style={{ fontSize: '10px', color: '#888' }}>{label}</div>
      <div style={{ fontSize: '18px', fontWeight: 700, color }}>{value}</div>
      {sub && <div style={{ fontSize: '10px', color: '#666' }}>{sub}</div>}
    </div>
  );
}

export default Monitor;
