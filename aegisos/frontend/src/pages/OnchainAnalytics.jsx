import React, { useState, useEffect, useCallback } from 'react';
import onchainService from '../services/onchainService';

function OnchainAnalytics() {
  const [tab, setTab] = useState('dashboard');
  const [dashboard, setDashboard] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [monitoring, setMonitoring] = useState(false);
  const [alertForm, setAlertForm] = useState({ metric_type: 'tps', condition: 'gt', threshold: 100, message: '' });
  const [autoRefresh, setAutoRefresh] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const [dash, al, mon] = await Promise.all([
        onchainService.dashboard(),
        onchainService.listAlerts(),
        onchainService.monitoringStatus(),
      ]);
      setDashboard(dash.data || null);
      setAlerts(al.data || []);
      setMonitoring(mon.data?.monitoring || false);
    } catch (err) { console.error(err); }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);
  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, [autoRefresh, fetchData]);

  const handleCreateAlert = async () => {
    try { await onchainService.createAlert(alertForm); setAlertForm({ ...alertForm, message: '' }); fetchData(); } catch (e) { console.error(e); }
  };
  const handleToggleMonitoring = async () => {
    try { if (monitoring) { await onchainService.stopMonitoring(); } else { await onchainService.startMonitoring(6); } fetchData(); } catch (e) { console.error(e); }
  };

  const panel = { background: '#1A1A1E', borderRadius: '10px', border: '1px solid #333', padding: '14px' };
  const btn = { padding: '8px 16px', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '13px', color: '#fff' };
  const input = { padding: '8px 12px', background: '#0D0D0F', border: '1px solid #333', borderRadius: '6px', color: '#fff', fontSize: '13px', width: '100%' };

  const metricLabels = { tps: 'TPS', block_time: 'Block Time', gas_used: 'Gas Used', tx_count: 'TX Count', peer_count: 'Peers', validator_count: 'Validators', block_size: 'Block Size', mempool_size: 'Mempool' };

  return (
    <div style={{ padding: '24px' }}>
      <h1 style={{ fontSize: '28px', fontWeight: 700, marginBottom: '4px' }}>📊 On-chain Analytics</h1>
      <p style={{ color: '#888', marginBottom: '12px' }}>Real-time blockchain metrics & insights</p>

      <div style={{ display: 'flex', gap: '4px', marginBottom: '12px' }}>
        {['dashboard', 'blocks', 'alerts'].map(t => (
          <button key={t} onClick={() => setTab(t)} style={{ ...btn, background: tab === t ? '#4F46E5' : '#1A1A1E', textTransform: 'capitalize' }}>{t}</button>
        ))}
        <button onClick={() => setAutoRefresh(!autoRefresh)} style={{ ...btn, background: autoRefresh ? '#22C55E' : '#1A1A1E' }}>{autoRefresh ? '⏸ Auto' : '▶ Auto'}</button>
        <button onClick={handleToggleMonitoring} style={{ ...btn, background: monitoring ? '#EF4444' : '#4F46E5' }}>{monitoring ? '⏹ Stop Monitor' : '▶ Start Monitor'}</button>
      </div>

      {tab === 'dashboard' && dashboard && (
        <div style={{ display: 'grid', gap: '12px' }}>
          {/* Metrics cards */}
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            {dashboard.metrics && Object.entries(dashboard.metrics).map(([key, val]) => (
              <div key={key} style={{ ...panel, flex: '1 1 120px', textAlign: 'center' }}>
                <div style={{ fontSize: '10px', color: '#888' }}>{metricLabels[key] || key}</div>
                <div style={{ fontSize: '18px', fontWeight: 700 }}>{typeof val.value === 'number' ? val.value.toFixed(2) : val.value}</div>
              </div>
            ))}
          </div>

          {/* TPS Trend */}
          {dashboard.tps_trend && (
            <div style={panel}>
              <div style={{ fontSize: '13px', fontWeight: 600, marginBottom: '8px' }}>TPS Trend</div>
              <div style={{ display: 'flex', gap: '12px', fontSize: '12px' }}>
                <span>Avg: <b style={{ color: '#4F46E5' }}>{dashboard.tps_trend.avg}</b></span>
                <span>Min: <b>{dashboard.tps_trend.min}</b></span>
                <span>Max: <b>{dashboard.tps_trend.max}</b></span>
                <span style={{ color: dashboard.tps_trend.trend === 'increasing' ? '#22C55E' : dashboard.tps_trend.trend === 'decreasing' ? '#EF4444' : '#888' }}>
                  Trend: {dashboard.tps_trend.trend}
                </span>
              </div>
              {/* Simple bar chart */}
              <div style={{ display: 'flex', alignItems: 'flex-end', height: '60px', gap: '2px', marginTop: '8px' }}>
                {dashboard.tps_trend.values?.map((v, i) => (
                  <div key={i} style={{ flex: 1, background: '#4F46E5', height: `${Math.min(100, (v / (dashboard.tps_trend.max || 1)) * 100)}%`, borderRadius: '2px 2px 0 0', minHeight: '2px' }} />
                ))}
              </div>
            </div>
          )}

          {/* Gas Analytics */}
          {dashboard.gas_analytics && (
            <div style={panel}>
              <div style={{ fontSize: '13px', fontWeight: 600, marginBottom: '4px' }}>Gas Analytics</div>
              <div style={{ fontSize: '12px', color: '#888' }}>
                Avg: {dashboard.gas_analytics.avg?.toFixed(0)} | Utilization: {dashboard.gas_analytics.utilization}% | Max: {dashboard.gas_analytics.max?.toFixed(0)}
              </div>
            </div>
          )}

          {/* Block Analytics */}
          {dashboard.block_analytics && (
            <div style={panel}>
              <div style={{ fontSize: '13px', fontWeight: 600, marginBottom: '4px' }}>Block Analytics</div>
              <div style={{ fontSize: '12px', color: '#888' }}>
                Latest: #{dashboard.block_analytics.latest_height} | Avg TX: {dashboard.block_analytics.avg_tx_count} | Avg Size: {dashboard.block_analytics.avg_size_bytes?.toFixed(0)} bytes
              </div>
            </div>
          )}
        </div>
      )}

      {tab === 'blocks' && dashboard && (
        <div style={{ display: 'grid', gap: '6px' }}>
          {dashboard.recent_blocks?.map((b, i) => (
            <div key={i} style={panel}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <div style={{ fontSize: '13px', fontWeight: 600 }}>#{b.height}</div>
                <span style={{ fontSize: '10px', color: '#888' }}>{new Date(b.timestamp).toLocaleTimeString()}</span>
              </div>
              <div style={{ fontSize: '10px', fontFamily: 'monospace', color: '#4F46E5' }}>{b.hash?.substring(0, 30)}...</div>
              <div style={{ fontSize: '10px', color: '#888', marginTop: '4px' }}>
                TX: {b.tx_count} | Gas: {b.gas_used?.toLocaleString()} | Size: {b.block_size_bytes} bytes
              </div>
            </div>
          ))}
          {(!dashboard.recent_blocks || dashboard.recent_blocks.length === 0) && (
            <div style={{ fontSize: '12px', color: '#888' }}>No blocks yet. Click "Collect" or start monitoring.</div>
          )}
        </div>
      )}

      {tab === 'alerts' && (
        <div style={{ display: 'grid', gap: '12px' }}>
          <div style={{ ...panel, maxWidth: '500px' }}>
            <div style={{ fontSize: '14px', fontWeight: 600, marginBottom: '12px' }}>Create Alert</div>
            <div style={{ display: 'grid', gap: '8px' }}>
              <select value={alertForm.metric_type} onChange={e => setAlertForm({ ...alertForm, metric_type: e.target.value })} style={input}>
                <option value="tps">TPS</option><option value="block_time">Block Time</option><option value="gas_used">Gas Used</option>
                <option value="tx_count">TX Count</option><option value="block_size">Block Size</option>
              </select>
              <select value={alertForm.condition} onChange={e => setAlertForm({ ...alertForm, condition: e.target.value })} style={input}>
                <option value="gt">&gt; Greater than</option><option value="lt">&lt; Less than</option>
              </select>
              <input type="number" value={alertForm.threshold} onChange={e => setAlertForm({ ...alertForm, threshold: parseFloat(e.target.value) })} style={input} />
              <input value={alertForm.message} onChange={e => setAlertForm({ ...alertForm, message: e.target.value })} placeholder="Alert message" style={input} />
              <button onClick={handleCreateAlert} style={{ ...btn, background: '#4F46E5' }}>Create Alert</button>
            </div>
          </div>

          {alerts.map((a, i) => (
            <div key={i} style={panel}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ fontSize: '12px' }}>{a.metric_type} {a.condition} {a.threshold}</div>
                <span style={{ fontSize: '10px', padding: '2px 6px', borderRadius: '4px', background: a.triggered ? '#EF444422' : '#22C55E22', color: a.triggered ? '#EF4444' : '#22C55E' }}>
                  {a.triggered ? '⚠ Triggered' : '✓ Active'}
                </span>
              </div>
              <div style={{ fontSize: '10px', color: '#888', marginTop: '4px' }}>{a.message}</div>
            </div>
          ))}
          {alerts.length === 0 && <div style={{ fontSize: '12px', color: '#888' }}>No alerts</div>}
        </div>
      )}
    </div>
  );
}

export default OnchainAnalytics;
