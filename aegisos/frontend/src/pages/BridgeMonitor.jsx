import React, { useState, useEffect, useCallback } from 'react';
import bridgeService from '../services/bridgeService';

function BridgeMonitor() {
  const [tab, setTab] = useState('overview');
  const [dashboard, setDashboard] = useState(null);
  const [transfers, setTransfers] = useState([]);
  const [relayers, setRelayers] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [monitoring, setMonitoring] = useState(false);
  const [trForm, setTrForm] = useState({ direction: 'inbound', source_chain: 'ethereum', target_chain: 'verdis', sender: '', recipient: '', amount: 0, token: 'VRS', fee: 0 });
  const [autoRefresh, setAutoRefresh] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const [dash, trs, rels, alts, mon] = await Promise.all([
        bridgeService.dashboard(),
        bridgeService.listTransfers({ limit: 20 }),
        bridgeService.listRelayers(true),
        bridgeService.listAlerts(),
        bridgeService.monitoringStatus(),
      ]);
      setDashboard(dash.data || null);
      setTransfers(trs.data || []);
      setRelayers(rels.data || []);
      setAlerts(alts.data || []);
      setMonitoring(mon.data?.monitoring || false);
    } catch (err) { console.error(err); }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);
  useEffect(() => {
    if (!autoRefresh) return;
    const i = setInterval(fetchData, 5000);
    return () => clearInterval(i);
  }, [autoRefresh, fetchData]);

  const handleCreateTransfer = async () => {
    try { await bridgeService.createTransfer(trForm); setTrForm({ ...trForm, sender: '', recipient: '', amount: 0 }); fetchData(); } catch (e) { console.error(e); }
  };

  const fmt = (n) => n >= 1e9 ? `${(n/1e9).toFixed(2)}B` : n >= 1e6 ? `${(n/1e6).toFixed(2)}M` : n >= 1e3 ? `${(n/1e3).toFixed(1)}K` : n.toFixed(2);
  const statusColor = { operational: '#22C55E', degraded: '#FFA500', maintenance: '#4F46E5', down: '#EF4444', pending: '#FFA500', validated: '#4F46E5', executed: '#22C55E', failed: '#EF4444', refunded: '#888' };
  const panel = { background: '#1A1A1E', borderRadius: '10px', border: '1px solid #333', padding: '14px' };
  const btn = { padding: '8px 16px', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '13px', color: '#fff' };
  const input = { padding: '8px 12px', background: '#0D0D0F', border: '1px solid #333', borderRadius: '6px', color: '#fff', fontSize: '13px', width: '100%' };

  return (
    <div style={{ padding: '24px' }}>
      <h1 style={{ fontSize: '28px', fontWeight: 700, marginBottom: '4px' }}>🌉 Bridge Monitor</h1>
      <p style={{ color: '#888', marginBottom: '12px' }}>Cross-chain transfers, relayers & alerts</p>

      <div style={{ display: 'flex', gap: '4px', marginBottom: '12px' }}>
        {['overview', 'transfers', 'relayers', 'alerts'].map(t => (
          <button key={t} onClick={() => setTab(t)} style={{ ...btn, background: tab === t ? '#4F46E5' : '#1A1A1E', textTransform: 'capitalize' }}>{t}</button>
        ))}
        <button onClick={() => setAutoRefresh(!autoRefresh)} style={{ ...btn, background: autoRefresh ? '#22C55E' : '#1A1A1E' }}>{autoRefresh ? '⏸ Auto' : '▶ Auto'}</button>
        <button onClick={async () => { if (monitoring) { await bridgeService.stopMonitoring(); } else { await bridgeService.startMonitoring(10); } fetchData(); }} style={{ ...btn, background: monitoring ? '#EF4444' : '#4F46E5' }}>{monitoring ? '⏹ Monitor' : '▶ Monitor'}</button>
      </div>

      {tab === 'overview' && dashboard && (
        <div style={{ display: 'grid', gap: '12px' }}>
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            {[{ l: 'Status', v: dashboard.health?.status, c: statusColor[dashboard.health?.status] }, { l: 'Relayers', v: `${dashboard.health?.active_relayers}/${dashboard.health?.total_relayers}` }, { l: 'Success Rate', v: `${dashboard.health?.success_rate}%` }, { l: 'Avg Latency', v: `${dashboard.health?.avg_latency_ms}ms` }, { l: 'Total Transfers', v: dashboard.health?.total_transfers }, { l: 'Total Volume', v: fmt(dashboard.health?.total_volume || 0) }].map(s => (
              <div key={s.l} style={{ ...panel, flex: '1 1 120px', textAlign: 'center' }}>
                <div style={{ fontSize: '10px', color: '#888' }}>{s.l}</div>
                <div style={{ fontSize: '16px', fontWeight: 700, color: s.c || '#fff' }}>{s.v}</div>
              </div>
            ))}
          </div>

          {dashboard.transfer_stats && (
            <div style={panel}>
              <div style={{ fontSize: '13px', fontWeight: 600, marginBottom: '8px' }}>Transfer Stats</div>
              <div style={{ display: 'flex', gap: '16px', fontSize: '12px', color: '#888', flexWrap: 'wrap' }}>
                <span>Executed: <b style={{ color: '#22C55E' }}>{dashboard.transfer_stats.executed}</b></span>
                <span>Pending: <b style={{ color: '#FFA500' }}>{dashboard.transfer_stats.pending}</b></span>
                <span>Validated: <b style={{ color: '#4F46E5' }}>{dashboard.transfer_stats.validated}</b></span>
                <span>Failed: <b style={{ color: '#EF4444' }}>{dashboard.transfer_stats.failed}</b></span>
                <span>Fees: <b>{fmt(dashboard.transfer_stats.total_fees || 0)}</b></span>
              </div>
            </div>
          )}

          <div style={panel}>
            <div style={{ fontSize: '13px', fontWeight: 600, marginBottom: '8px' }}>Recent Transfers</div>
            {dashboard.recent_transfers?.map((t, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', borderBottom: '1px solid #222' }}>
                <div style={{ fontSize: '11px' }}>{t.source_chain} → {t.target_chain}</div>
                <div style={{ fontSize: '11px', fontWeight: 600 }}>{fmt(t.amount)} {t.token}</div>
                <span style={{ fontSize: '9px', padding: '1px 6px', borderRadius: '4px', background: (statusColor[t.status] || '#888') + '22', color: statusColor[t.status] || '#888' }}>{t.status}</span>
              </div>
            ))}
            {(!dashboard.recent_transfers || dashboard.recent_transfers.length === 0) && <div style={{ fontSize: '12px', color: '#888' }}>No transfers</div>}
          </div>
        </div>
      )}

      {tab === 'transfers' && (
        <div style={{ display: 'grid', gap: '12px' }}>
          <div style={{ ...panel, maxWidth: '600px' }}>
            <div style={{ fontSize: '14px', fontWeight: 600, marginBottom: '12px' }}>Create Bridge Transfer</div>
            <div style={{ display: 'grid', gap: '8px' }}>
              <div style={{ display: 'flex', gap: '8px' }}>
                <select value={trForm.direction} onChange={e => setTrForm({ ...trForm, direction: e.target.value })} style={input}>
                  <option value="inbound">Inbound</option><option value="outbound">Outbound</option>
                </select>
                <input value={trForm.source_chain} onChange={e => setTrForm({ ...trForm, source_chain: e.target.value })} placeholder="Source chain" style={input} />
                <input value={trForm.target_chain} onChange={e => setTrForm({ ...trForm, target_chain: e.target.value })} placeholder="Target chain" style={input} />
              </div>
              <input value={trForm.sender} onChange={e => setTrForm({ ...trForm, sender: e.target.value })} placeholder="Sender" style={input} />
              <input value={trForm.recipient} onChange={e => setTrForm({ ...trForm, recipient: e.target.value })} placeholder="Recipient" style={input} />
              <div style={{ display: 'flex', gap: '8px' }}>
                <input type="number" value={trForm.amount} onChange={e => setTrForm({ ...trForm, amount: parseFloat(e.target.value) })} placeholder="Amount" style={input} />
                <input value={trForm.token} onChange={e => setTrForm({ ...trForm, token: e.target.value })} placeholder="Token" style={input} />
              </div>
              <button onClick={handleCreateTransfer} style={{ ...btn, background: '#4F46E5' }}>Create Transfer</button>
            </div>
          </div>
          {transfers.map((t, i) => (
            <div key={i} style={panel}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <div style={{ fontSize: '12px', fontWeight: 600 }}>{t.source_chain} → {t.target_chain}</div>
                <span style={{ fontSize: '9px', padding: '2px 6px', borderRadius: '4px', background: (statusColor[t.status] || '#888') + '22', color: statusColor[t.status] || '#888' }}>{t.status}</span>
              </div>
              <div style={{ fontSize: '11px', color: '#888', marginTop: '4px' }}>{fmt(t.amount)} {t.token} | Sigs: {t.validator_signatures}/{t.required_signatures}</div>
              <div style={{ fontSize: '10px', color: '#666' }}>{new Date(t.created).toLocaleString()}</div>
            </div>
          ))}
        </div>
      )}

      {tab === 'relayers' && (
        <div style={{ display: 'grid', gap: '8px' }}>
          {relayers.map((r, i) => (
            <div key={i} style={panel}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <div style={{ fontSize: '13px', fontWeight: 600 }}>{r.name}</div>
                <span style={{ fontSize: '10px', padding: '2px 6px', borderRadius: '4px', background: r.active ? '#22C55E22' : '#EF444422', color: r.active ? '#22C55E' : '#EF4444' }}>{r.active ? 'Active' : 'Offline'}</span>
              </div>
              <div style={{ fontSize: '10px', fontFamily: 'monospace', color: '#4F46E5' }}>{r.address?.substring(0, 24)}...</div>
              <div style={{ fontSize: '10px', color: '#888', marginTop: '4px' }}>Relayed: {r.transfers_relayed} | Success: {r.success_rate}% | Latency: {r.latency_ms}ms</div>
            </div>
          ))}
        </div>
      )}

      {tab === 'alerts' && (
        <div style={{ display: 'grid', gap: '8px' }}>
          {alerts.map((a, i) => (
            <div key={i} style={panel}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <div style={{ fontSize: '12px', fontWeight: 600 }}>{a.alert_type.replace('_', ' ')}</div>
                <div style={{ display: 'flex', gap: '4px', alignItems: 'center' }}>
                  <span style={{ fontSize: '9px', padding: '2px 6px', borderRadius: '4px', background: a.severity === 'critical' ? '#EF444422' : a.severity === 'high' ? '#FFA50022' : '#4F46E522', color: a.severity === 'critical' ? '#EF4444' : a.severity === 'high' ? '#FFA500' : '#4F46E5' }}>{a.severity}</span>
                  <span style={{ fontSize: '9px', padding: '2px 6px', borderRadius: '4px', background: a.triggered ? '#EF444422' : '#22C55E22', color: a.triggered ? '#EF4444' : '#22C55E' }}>{a.triggered ? '⚠ Triggered' : '✓ Active'}</span>
                </div>
              </div>
              <div style={{ fontSize: '11px', color: '#888', marginTop: '4px' }}>{a.message}</div>
              <div style={{ fontSize: '10px', color: '#666' }}>Threshold: {a.threshold}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default BridgeMonitor;
