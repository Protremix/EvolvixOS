import React, { useState, useEffect, useCallback } from 'react';
import verdisProjectService from '../services/verdisProjectService';

function VerdisProject() {
  const [overview, setOverview] = useState(null);
  const [stats, setStats] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [healthSummary, setHealthSummary] = useState('');
  const [loading, setLoading] = useState(true);
  const [checking, setChecking] = useState(false);

  const fetchAll = useCallback(async () => {
    try {
      const [ovResp, statsResp, alertsResp, summaryResp] = await Promise.all([
        verdisProjectService.overview(),
        verdisProjectService.stats(),
        verdisProjectService.alerts(false),
        verdisProjectService.healthSummary(),
      ]);
      setOverview(ovResp.data);
      setStats(statsResp.data);
      setAlerts(alertsResp.data);
      setHealthSummary(summaryResp.data.summary);
    } catch (err) { console.error('Failed', err); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  const handleRegister = async () => {
    await verdisProjectService.register();
    fetchAll();
  };

  const handleHealthCheck = async () => {
    setChecking(true);
    try { await verdisProjectService.healthCheck(); fetchAll(); }
    catch (err) { console.error(err); }
    finally { setChecking(false); }
  };

  if (loading) return <div style={{ padding: '24px', color: '#888' }}>Loading Verdis project...</div>;

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '24px' }}>
        <div>
          <h1 style={{ fontSize: '28px', fontWeight: 700, margin: '0 0 4px' }}>🌱 Verdis Blockchain</h1>
          <p style={{ color: '#888' }}>World's first fully green, carbon-negative blockchain — managed by EvolvixOS</p>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          {!overview?.registered && <button onClick={handleRegister} style={btnPrimary}>Register Project</button>}
          <button onClick={handleHealthCheck} disabled={checking} style={btnPrimary}>
            {checking ? 'Checking...' : 'Run Health Check'}
          </button>
        </div>
      </div>

      {/* Stats Grid */}
      {stats && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(120px, 1fr))', gap: '12px', marginBottom: '24px' }}>
          <StatCard label="Registered" value={stats.registered ? '✓' : '✗'} color={stats.registered ? '#22C55E' : '#EF4444'} />
          <StatCard label="Monitoring" value={stats.monitoring_enabled ? 'ON' : 'OFF'} color={stats.monitoring_enabled ? '#22C55E' : '#888'} />
          <StatCard label="Snapshots" value={stats.total_snapshots} />
          <StatCard label="Components" value={stats.components_tracked} color="#4F46E5" />
          <StatCard label="Active Alerts" value={stats.active_alerts} color={stats.active_alerts > 0 ? '#FFA500' : '#22C55E'} />
        </div>
      )}

      {/* Health Snapshot */}
      {overview?.health && (
        <div style={{ ...panelStyle, marginBottom: '16px' }}>
          <h3 style={{ margin: '0 0 12px', fontSize: '16px' }}>Latest Health Snapshot</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))', gap: '8px' }}>
            <HealthItem label="Connected" value={overview.health.connected ? '✓ Yes' : '✗ No'} color={overview.health.connected ? '#22C55E' : '#EF4444'} />
            <HealthItem label="Block Height" value={overview.health.block_height || 'Unknown'} />
            <HealthItem label="Peers" value={overview.health.peers || 0} />
            <HealthItem label="Validators" value={overview.health.validator_count || 0} color={overview.health.validator_count >= 10 ? '#22C55E' : '#FFA500'} />
            <HealthItem label="Spec Version" value={overview.health.spec_version || 'Unknown'} />
            <HealthItem label="RPC Methods" value={overview.health.rpc_method_count || 0} />
            <HealthItem label="Syncing" value={overview.health.is_syncing ? 'Yes' : 'No'} />
            <HealthItem label="Node" value={overview.health.node_name || 'Unknown'} />
          </div>
        </div>
      )}

      {/* Ecosystem Components */}
      {overview?.components && (
        <div style={{ ...panelStyle, marginBottom: '16px' }}>
          <h3 style={{ margin: '0 0 12px', fontSize: '16px' }}>Ecosystem Components ({overview.components.length})</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            {overview.components.map(c => (
              <div key={c.name} style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '8px 12px', background: '#0D0D0F', borderRadius: '6px' }}>
                <span style={{ ...badgeStyle, background: statusColor(c.status) + '22', color: statusColor(c.status) }}>{c.status}</span>
                <span style={{ fontSize: '13px', fontWeight: 600, minWidth: '180px' }}>{c.name}</span>
                <span style={{ fontSize: '11px', color: '#555', minWidth: '60px' }}>{c.type}</span>
                <span style={{ fontSize: '11px', color: '#4F46E5' }}>{c.version}</span>
                <span style={{ fontSize: '11px', color: '#666', flex: 1 }}>{c.notes}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Active Alerts */}
      {alerts.length > 0 && (
        <div style={{ ...panelStyle, marginBottom: '16px' }}>
          <h3 style={{ margin: '0 0 12px', fontSize: '16px' }}>Active Alerts ({alerts.length})</h3>
          {alerts.map(a => (
            <div key={a.id} style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '8px 12px', marginBottom: '4px', background: '#0D0D0F', borderRadius: '6px' }}>
              <span style={{ ...badgeStyle, background: severityColor(a.severity) + '22', color: severityColor(a.severity), textTransform: 'uppercase' }}>{a.severity}</span>
              <span style={{ fontSize: '11px', color: '#888', minWidth: '80px' }}>{a.category}</span>
              <span style={{ fontSize: '13px', color: '#CCC', flex: 1 }}>{a.message}</span>
              <button onClick={async () => { await verdisProjectService.resolveAlert(a.id); fetchAll(); }} style={btnSmall}>Resolve</button>
            </div>
          ))}
        </div>
      )}

      {/* Pipeline Template */}
      {overview?.pipeline_template && (
        <div style={{ ...panelStyle, marginBottom: '16px' }}>
          <h3 style={{ margin: '0 0 12px', fontSize: '16px' }}>Verdis Pipeline Template</h3>
          <div style={{ fontSize: '13px', fontWeight: 600, marginBottom: '8px' }}>{overview.pipeline_template.name}</div>
          <div style={{ fontSize: '12px', color: '#888', marginBottom: '8px' }}>{overview.pipeline_template.description}</div>
          <div style={{ fontSize: '11px', color: '#666', marginBottom: '4px' }}>Constraints:</div>
          {overview.pipeline_template.default_constraints.map((c, i) => (
            <div key={i} style={{ fontSize: '11px', color: '#4F46E5', paddingLeft: '12px' }}>• {c}</div>
          ))}
        </div>
      )}

      {/* Health Summary */}
      {healthSummary && (
        <div style={{ ...panelStyle, marginBottom: '16px' }}>
          <h3 style={{ margin: '0 0 12px', fontSize: '16px' }}>Health Summary (from RPC)</h3>
          <pre style={{ fontSize: '12px', color: '#AAA', whiteSpace: 'pre-wrap', fontFamily: 'monospace', margin: 0 }}>{healthSummary}</pre>
        </div>
      )}
    </div>
  );
}

function StatCard({ label, value, color }) {
  return (
    <div style={{ background: '#1A1A1E', borderRadius: '10px', padding: '12px', border: '1px solid #333' }}>
      <div style={{ fontSize: '11px', color: '#888' }}>{label}</div>
      <div style={{ fontSize: '20px', fontWeight: 700, color: color || '#fff', marginTop: '2px' }}>{value}</div>
    </div>
  );
}

function HealthItem({ label, value, color }) {
  return (
    <div style={{ background: '#0D0D0F', borderRadius: '6px', padding: '8px 10px' }}>
      <div style={{ fontSize: '10px', color: '#666' }}>{label}</div>
      <div style={{ fontSize: '14px', fontWeight: 600, color: color || '#CCC', marginTop: '2px' }}>{value}</div>
    </div>
  );
}

const statusColor = (s) => s === 'healthy' ? '#22C55E' : s === 'degraded' ? '#FFA500' : s === 'offline' ? '#EF4444' : '#888';
const severityColor = (s) => s === 'critical' ? '#EF4444' : s === 'warning' ? '#FFA500' : '#4F46E5';

const panelStyle = { background: '#1A1A1E', borderRadius: '10px', padding: '16px', border: '1px solid #333' };
const btnPrimary = { padding: '8px 16px', background: '#4F46E5', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer' };
const btnSmall = { padding: '4px 12px', background: '#2A2A2E', color: '#CCC', border: '1px solid #333', borderRadius: '4px', cursor: 'pointer', fontSize: '12px' };
const badgeStyle = { fontSize: '9px', padding: '2px 6px', borderRadius: '4px', fontWeight: 600, minWidth: '50px', textAlign: 'center' };

export default VerdisProject;
