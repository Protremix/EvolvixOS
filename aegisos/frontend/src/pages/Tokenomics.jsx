import React, { useState, useEffect, useCallback } from 'react';
import tokenomicsService from '../services/tokenomicsService';

function Tokenomics() {
  const [tab, setTab] = useState('overview');
  const [dashboard, setDashboard] = useState(null);
  const [allocations, setAllocations] = useState([]);
  const [vesting, setVesting] = useState([]);
  const [flows, setFlows] = useState([]);
  const [chart, setChart] = useState(null);
  const [vestForm, setVestForm] = useState({ beneficiary: '', allocation_type: 'investors', total_amount: 0, vesting_months: 48, cliff_months: 12 });

  const fetchData = useCallback(async () => {
    try {
      const [dash, allocs, vests, flws, chrt] = await Promise.all([
        tokenomicsService.dashboard(),
        tokenomicsService.allocations(),
        tokenomicsService.listVesting({}),
        tokenomicsService.listFlows({ limit: 20 }),
        tokenomicsService.distributionChart(),
      ]);
      setDashboard(dash.data || null);
      setAllocations(allocs.data || []);
      setVesting(vests.data || []);
      setFlows(flws.data || []);
      setChart(chrt.data || null);
    } catch (err) { console.error(err); }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleCreateVesting = async () => {
    try { await tokenomicsService.createVesting(vestForm); setVestForm({ ...vestForm, beneficiary: '', total_amount: 0 }); fetchData(); } catch (e) { console.error(e); }
  };

  const fmt = (n) => n >= 1e9 ? `${(n/1e9).toFixed(2)}B` : n >= 1e6 ? `${(n/1e6).toFixed(2)}M` : n >= 1e3 ? `${(n/1e3).toFixed(2)}K` : n.toFixed(2);
  const panel = { background: '#1A1A1E', borderRadius: '10px', border: '1px solid #333', padding: '14px' };
  const btn = { padding: '8px 16px', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '13px', color: '#fff' };
  const input = { padding: '8px 12px', background: '#0D0D0F', border: '1px solid #333', borderRadius: '6px', color: '#fff', fontSize: '13px', width: '100%' };

  return (
    <div style={{ padding: '24px' }}>
      <h1 style={{ fontSize: '28px', fontWeight: 700, marginBottom: '4px' }}>💰 Tokenomics</h1>
      <p style={{ color: '#888', marginBottom: '20px' }}>Supply, Distribution, Vesting & Token Flow</p>

      <div style={{ display: 'flex', gap: '4px', marginBottom: '16px' }}>
        {['overview', 'allocations', 'vesting', 'flows'].map(t => (
          <button key={t} onClick={() => setTab(t)} style={{ ...btn, background: tab === t ? '#4F46E5' : '#1A1A1E', textTransform: 'capitalize' }}>{t}</button>
        ))}
      </div>

      {tab === 'overview' && dashboard && (
        <div style={{ display: 'grid', gap: '12px' }}>
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            {[{ l: 'Total Supply', v: fmt(dashboard.total_supply) }, { l: 'Circulating', v: fmt(dashboard.circulating_supply) }, { l: 'Locked', v: fmt(dashboard.supply?.locked) }, { l: 'Burned', v: fmt(dashboard.utility?.burned) }, { l: 'Staked', v: fmt(dashboard.utility?.staked_amount) }, { l: 'Investor Alloc', v: fmt(dashboard.investor_allocation) }].map(s => (
              <div key={s.l} style={{ ...panel, flex: '1 1 120px', textAlign: 'center' }}>
                <div style={{ fontSize: '10px', color: '#888' }}>{s.l}</div>
                <div style={{ fontSize: '16px', fontWeight: 700 }}>{s.v}</div>
              </div>
            ))}
          </div>

          {chart && (
            <div style={panel}>
              <div style={{ fontSize: '13px', fontWeight: 600, marginBottom: '12px' }}>Token Distribution</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {chart.labels.map((label, i) => (
                  <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <div style={{ width: '12px', height: '12px', borderRadius: '3px', background: chart.colors[i] }} />
                    <div style={{ fontSize: '11px', flex: 1 }}>{label}</div>
                    <div style={{ fontSize: '11px', fontWeight: 600 }}>{fmt(chart.values[i])} VRS</div>
                    <div style={{ fontSize: '10px', color: '#888', width: '40px', textAlign: 'right' }}>{((chart.values[i] / dashboard.total_supply) * 100).toFixed(1)}%</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div style={panel}>
            <div style={{ fontSize: '13px', fontWeight: 600, marginBottom: '8px' }}>Supply Metrics</div>
            <div style={{ fontSize: '12px', color: '#888' }}>
              Circulating: {dashboard.circulating_pct}% | Locked: {dashboard.supply?.locked_pct}%
            </div>
          </div>
        </div>
      )}

      {tab === 'allocations' && (
        <div style={{ display: 'grid', gap: '8px' }}>
          {allocations.map((a, i) => (
            <div key={i} style={panel}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <div style={{ fontSize: '13px', fontWeight: 600, textTransform: 'capitalize' }}>{a.type}</div>
                <span style={{ fontSize: '11px', fontWeight: 600 }}>{a.percentage}%</span>
              </div>
              <div style={{ fontSize: '11px', color: '#888', marginTop: '4px' }}>{a.description}</div>
              <div style={{ display: 'flex', gap: '12px', fontSize: '11px', marginTop: '4px' }}>
                <span style={{ color: '#22C55E' }}>Released: {fmt(a.released)}</span>
                <span style={{ color: '#FFA500' }}>Locked: {fmt(a.locked)}</span>
                <span style={{ color: '#666' }}>Total: {fmt(a.total_amount)}</span>
              </div>
              {a.vesting_months > 0 && <div style={{ fontSize: '10px', color: '#666', marginTop: '2px' }}>Vesting: {a.vesting_months} months | Cliff: {a.cliff_months} months</div>}
            </div>
          ))}
        </div>
      )}

      {tab === 'vesting' && (
        <div style={{ display: 'grid', gap: '12px' }}>
          <div style={{ ...panel, maxWidth: '500px' }}>
            <div style={{ fontSize: '14px', fontWeight: 600, marginBottom: '12px' }}>Create Vesting Schedule</div>
            <div style={{ display: 'grid', gap: '8px' }}>
              <input value={vestForm.beneficiary} onChange={e => setVestForm({ ...vestForm, beneficiary: e.target.value })} placeholder="Beneficiary address" style={input} />
              <select value={vestForm.allocation_type} onChange={e => setVestForm({ ...vestForm, allocation_type: e.target.value })} style={input}>
                <option value="investors">Investors</option><option value="team">Team</option><option value="ecosystem">Ecosystem</option>
              </select>
              <div style={{ display: 'flex', gap: '8px' }}>
                <input type="number" value={vestForm.total_amount} onChange={e => setVestForm({ ...vestForm, total_amount: parseFloat(e.target.value) })} placeholder="Amount" style={input} />
                <input type="number" value={vestForm.vesting_months} onChange={e => setVestForm({ ...vestForm, vesting_months: parseInt(e.target.value) })} placeholder="Months" style={input} />
                <input type="number" value={vestForm.cliff_months} onChange={e => setVestForm({ ...vestForm, cliff_months: parseInt(e.target.value) })} placeholder="Cliff" style={input} />
              </div>
              <button onClick={handleCreateVesting} style={{ ...btn, background: '#4F46E5' }}>Create</button>
            </div>
          </div>
          {vesting.map((v, i) => (
            <div key={i} style={panel}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <div style={{ fontSize: '12px' }}>{v.beneficiary?.substring(0, 20)}...</div>
                <span style={{ fontSize: '10px', padding: '2px 6px', borderRadius: '4px', background: '#4F46E522', color: '#4F46E5' }}>{v.status}</span>
              </div>
              <div style={{ fontSize: '11px', color: '#888' }}>Total: {fmt(v.total_amount)} | Released: {fmt(v.released)}</div>
              <div style={{ fontSize: '10px', color: '#666' }}>Monthly: {fmt(v.monthly_release)} VRS</div>
            </div>
          ))}
        </div>
      )}

      {tab === 'flows' && (
        <div style={{ display: 'grid', gap: '6px' }}>
          {flows.map((f, i) => (
            <div key={i} style={panel}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ fontSize: '11px', fontWeight: 600, textTransform: 'capitalize' }}>{f.flow_type.replace('_', ' ')}</span>
                <span style={{ fontSize: '12px', fontWeight: 700, color: '#4F46E5' }}>{fmt(f.amount)} VRS</span>
              </div>
              <div style={{ fontSize: '10px', color: '#888', marginTop: '4px' }}>
                {f.from_addr?.substring(0, 12)}... → {f.to_addr?.substring(0, 12)}...
              </div>
              <div style={{ fontSize: '10px', color: '#666' }}>{new Date(f.timestamp).toLocaleString()}</div>
            </div>
          ))}
          {flows.length === 0 && <div style={{ fontSize: '12px', color: '#888' }}>No token flows recorded</div>}
        </div>
      )}
    </div>
  );
}

export default Tokenomics;
