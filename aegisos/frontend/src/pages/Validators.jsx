import React, { useState, useEffect, useCallback } from 'react';
import validatorService from '../services/validatorService';

function Validators() {
  const [tab, setTab] = useState('list');
  const [dashboard, setDashboard] = useState(null);
  const [validators, setValidators] = useState([]);
  const [delegations, setDelegations] = useState([]);
  const [events, setEvents] = useState([]);
  const [monitoring, setMonitoring] = useState(false);
  const [sortBy, setSortBy] = useState('stake');
  const [delForm, setDelForm] = useState({ delegator: '', validator_id: '', amount: 0 });
  const [autoRefresh, setAutoRefresh] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const [dash, vals, mon, evs] = await Promise.all([
        validatorService.dashboard(),
        validatorService.list({ sort_by: sortBy, limit: 101 }),
        validatorService.monitoringStatus(),
        validatorService.recentEvents(20),
      ]);
      setDashboard(dash.data || null);
      setValidators(vals.data || []);
      setMonitoring(mon.data?.monitoring || false);
      setEvents(evs.data || []);
    } catch (err) { console.error(err); }
  }, [sortBy]);

  useEffect(() => { fetchData(); }, [fetchData]);
  useEffect(() => {
    if (!autoRefresh) return;
    const i = setInterval(fetchData, 5000);
    return () => clearInterval(i);
  }, [autoRefresh, fetchData]);

  const handleDelegate = async () => {
    try { await validatorService.delegate(delForm); setDelForm({ ...delForm, amount: 0, delegator: '' }); fetchData(); } catch (e) { console.error(e); }
  };

  const fmt = (n) => n >= 1e9 ? `${(n/1e9).toFixed(2)}B` : n >= 1e6 ? `${(n/1e6).toFixed(2)}M` : n >= 1e3 ? `${(n/1e3).toFixed(1)}K` : n.toFixed(2);
  const statusColor = { active: '#22C55E', paused: '#FFA500', slashed: '#EF4444', ejected: '#888', inactive: '#666' };
  const panel = { background: '#1A1A1E', borderRadius: '10px', border: '1px solid #333', padding: '14px' };
  const btn = { padding: '8px 16px', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '13px', color: '#fff' };
  const input = { padding: '8px 12px', background: '#0D0D0F', border: '1px solid #333', borderRadius: '6px', color: '#fff', fontSize: '13px', width: '100%' };

  return (
    <div style={{ padding: '24px' }}>
      <h1 style={{ fontSize: '28px', fontWeight: 700, marginBottom: '4px' }}>⚡ Validators</h1>
      <p style={{ color: '#888', marginBottom: '12px' }}>Network validators, staking & green scores</p>

      <div style={{ display: 'flex', gap: '4px', marginBottom: '12px' }}>
        {['list', 'delegate', 'events'].map(t => (
          <button key={t} onClick={() => setTab(t)} style={{ ...btn, background: tab === t ? '#4F46E5' : '#1A1A1E', textTransform: 'capitalize' }}>{t}</button>
        ))}
        <button onClick={() => setAutoRefresh(!autoRefresh)} style={{ ...btn, background: autoRefresh ? '#22C55E' : '#1A1A1E' }}>{autoRefresh ? '⏸ Auto' : '▶ Auto'}</button>
        <button onClick={async () => { if (monitoring) { await validatorService.stopMonitoring(); } else { await validatorService.startMonitoring(6); } fetchData(); }} style={{ ...btn, background: monitoring ? '#EF4444' : '#4F46E5' }}>{monitoring ? '⏹ Monitor' : '▶ Monitor'}</button>
      </div>

      {dashboard && tab === 'list' && (
        <div style={{ display: 'grid', gap: '12px' }}>
          {/* Stats */}
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            {[{ l: 'Active', v: dashboard.stats?.active_validators }, { l: 'Total Stake', v: fmt(dashboard.stats?.total_stake || 0) }, { l: 'Avg Green', v: `${dashboard.stats?.avg_green_score || 0}` }, { l: 'Avg Uptime', v: `${dashboard.stats?.avg_uptime || 0}%` }, { l: 'Certified', v: dashboard.stats?.certified_validators }, { l: 'Carbon Offset', v: `${fmt(dashboard.stats?.total_carbon_offset || 0)}t` }].map(s => (
              <div key={s.l} style={{ ...panel, flex: '1 1 100px', textAlign: 'center' }}>
                <div style={{ fontSize: '10px', color: '#888' }}>{s.l}</div>
                <div style={{ fontSize: '16px', fontWeight: 700 }}>{s.v}</div>
              </div>
            ))}
          </div>

          {/* Sort controls */}
          <div style={{ display: 'flex', gap: '4px' }}>
            {['stake', 'green', 'uptime', 'reward', 'blocks'].map(s => (
              <button key={s} onClick={() => setSortBy(s)} style={{ ...btn, background: sortBy === s ? '#4F46E5' : '#1A1A1E', fontSize: '11px', padding: '4px 8px' }}>{s}</button>
            ))}
          </div>

          {/* Validator list */}
          {validators.map((v, i) => (
            <div key={i} style={panel}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                <div>
                  <div style={{ fontSize: '13px', fontWeight: 600 }}>#{v.rank} {v.name}</div>
                  <div style={{ fontSize: '10px', fontFamily: 'monospace', color: '#4F46E5' }}>{v.address?.substring(0, 24)}...</div>
                </div>
                <div style={{ display: 'flex', gap: '4px', alignItems: 'center' }}>
                  {v.certified && <span style={{ fontSize: '9px', padding: '2px 6px', borderRadius: '4px', background: '#22C55E22', color: '#22C55E', fontWeight: 600 }}>CERTIFIED</span>}
                  <span style={{ fontSize: '9px', padding: '2px 6px', borderRadius: '4px', background: (statusColor[v.status] || '#888') + '22', color: statusColor[v.status] || '#888', fontWeight: 600 }}>{v.status}</span>
                </div>
              </div>
              <div style={{ display: 'flex', gap: '16px', fontSize: '11px', marginTop: '8px', color: '#888', flexWrap: 'wrap' }}>
                <span>Stake: <b style={{ color: '#fff' }}>{fmt(v.total_stake)}</b></span>
                <span>Green: <b style={{ color: v.green_score >= 80 ? '#22C55E' : '#FFA500' }}>{v.green_score}</b></span>
                <span>Uptime: <b style={{ color: '#fff' }}>{v.uptime_pct}%</b></span>
                <span>APY: <b style={{ color: '#4F46E5' }}>{v.reward_rate}%</b></span>
                <span>Commission: <b>{v.commission_rate}%</b></span>
                <span>Energy: <b>{v.energy_source}</b></span>
                <span>Carbon: <b>{v.carbon_offset}t</b></span>
                <span>Blocks: <b>{v.blocks_produced}</b></span>
              </div>
            </div>
          ))}
        </div>
      )}

      {tab === 'delegate' && (
        <div style={{ display: 'grid', gap: '12px' }}>
          <div style={{ ...panel, maxWidth: '500px' }}>
            <div style={{ fontSize: '14px', fontWeight: 600, marginBottom: '12px' }}>Delegate to Validator</div>
            <div style={{ display: 'grid', gap: '8px' }}>
              <select value={delForm.validator_id} onChange={e => setDelForm({ ...delForm, validator_id: e.target.value })} style={input}>
                <option value="">Select validator...</option>
                {validators.map(v => <option key={v.id} value={v.id}>{v.name} (APY {v.reward_rate}%)</option>)}
              </select>
              <input value={delForm.delegator} onChange={e => setDelForm({ ...delForm, delegator: e.target.value })} placeholder="Your address" style={input} />
              <input type="number" value={delForm.amount} onChange={e => setDelForm({ ...delForm, amount: parseFloat(e.target.value) })} placeholder="Amount VRS" style={input} />
              <button onClick={handleDelegate} style={{ ...btn, background: '#4F46E5' }}>Delegate</button>
            </div>
          </div>
          {delegations.map((d, i) => (
            <div key={i} style={panel}>
              <div style={{ fontSize: '12px' }}>{d.delegator?.substring(0, 20)}... → {d.validator_id}</div>
              <div style={{ fontSize: '11px', color: '#888' }}>Amount: {fmt(d.amount)} | Active: {d.active ? '✓' : '✗'}</div>
            </div>
          ))}
        </div>
      )}

      {tab === 'events' && (
        <div style={{ display: 'grid', gap: '6px' }}>
          {events.map((e, i) => (
            <div key={i} style={panel}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ fontSize: '11px', fontWeight: 600, textTransform: 'capitalize' }}>{e.event_type.replace('_', ' ')}</span>
                <span style={{ fontSize: '10px', color: '#888' }}>{new Date(e.timestamp).toLocaleString()}</span>
              </div>
              <div style={{ fontSize: '10px', color: '#666' }}>Validator: {e.validator_id?.substring(0, 16)}...</div>
            </div>
          ))}
          {events.length === 0 && <div style={{ fontSize: '12px', color: '#888' }}>No events</div>}
        </div>
      )}
    </div>
  );
}

export default Validators;
