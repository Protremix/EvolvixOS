import React, { useState, useEffect, useCallback } from 'react';
import stakingService from '../services/stakingService';

function StakingDashboard() {
  const [tab, setTab] = useState('overview');
  const [dashboard, setDashboard] = useState(null);
  const [validators, setValidators] = useState([]);
  const [positions, setPositions] = useState([]);
  const [calcInput, setCalcInput] = useState({ amount: 10000, apy: 17, days: 365, compound: false });
  const [calcResult, setCalcResult] = useState(null);
  const [stakeForm, setStakeForm] = useState({ delegator: '0xverdis', validator_id: 'val-001', amount: 1000, auto_compound: false });
  const [autoRefresh, setAutoRefresh] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const [dash, vals, pos] = await Promise.all([
        stakingService.dashboard('0xverdis'),
        stakingService.validators('total_staked'),
        stakingService.listPositions({ delegator: '0xverdis' }),
      ]);
      setDashboard(dash.data || null);
      setValidators(vals.data || []);
      setPositions(pos.data || []);
    } catch (err) { console.error(err); }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);
  useEffect(() => {
    if (!autoRefresh) return;
    const i = setInterval(fetchData, 10000);
    return () => clearInterval(i);
  }, [autoRefresh, fetchData]);

  const handleStake = async () => {
    try { await stakingService.stake(stakeForm); fetchData(); } catch (e) { console.error(e); }
  };

  const handleCalculate = async () => {
    try { const r = await stakingService.calculate(calcInput); setCalcResult(r.data); } catch (e) { console.error(e); }
  };

  const handleClaim = async (id) => {
    try { await stakingService.claimRewards(id); fetchData(); } catch (e) { console.error(e); }
  };

  const handleCompound = async (id) => {
    try { await stakingService.compoundRewards(id); fetchData(); } catch (e) { console.error(e); }
  };

  const handleUnstake = async (id) => {
    try { await stakingService.unstake(id); fetchData(); } catch (e) { console.error(e); }
  };

  const fmt = (n) => n >= 1e9 ? `${(n/1e9).toFixed(2)}B` : n >= 1e6 ? `${(n/1e6).toFixed(2)}M` : n >= 1e3 ? `${(n/1e3).toFixed(1)}K` : n.toFixed(2);
  const gradeColor = { A: '#22C55E', B: '#4F46E5', C: '#FFA500', D: '#EF4444' };
  const statusColor = { active: '#22C55E', unbonding: '#FFA500', withdrawn: '#888', slashed: '#EF4444' };
  const panel = { background: '#1A1A1E', borderRadius: '10px', border: '1px solid #333', padding: '14px' };
  const btn = { padding: '8px 16px', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '13px', color: '#fff' };
  const input = { padding: '8px 12px', background: '#0D0D0F', border: '1px solid #333', borderRadius: '6px', color: '#fff', fontSize: '13px', width: '100%' };

  return (
    <div style={{ padding: '24px' }}>
      <h1 style={{ fontSize: '28px', fontWeight: 700, marginBottom: '4px' }}>💎 Staking Dashboard</h1>
      <p style={{ color: '#888', marginBottom: '12px' }}>Manage stakes, track rewards, explore validators</p>

      <div style={{ display: 'flex', gap: '4px', marginBottom: '12px' }}>
        {['overview', 'validators', 'positions', 'calculator'].map(t => (
          <button key={t} onClick={() => setTab(t)} style={{ ...btn, background: tab === t ? '#4F46E5' : '#1A1A1E', textTransform: 'capitalize' }}>{t}</button>
        ))}
        <button onClick={() => setAutoRefresh(!autoRefresh)} style={{ ...btn, background: autoRefresh ? '#22C55E' : '#1A1A1E' }}>{autoRefresh ? '⏸ Auto' : '▶ Auto'}</button>
      </div>

      {tab === 'overview' && dashboard && (
        <div style={{ display: 'grid', gap: '12px' }}>
          {/* Network Stats */}
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            {[
              { l: 'Total Staked', v: fmt(dashboard.network?.total_staked || 0) },
              { l: 'Staking Ratio', v: `${dashboard.network?.staking_ratio}%` },
              { l: 'Validators', v: `${dashboard.network?.active_validators}/${dashboard.network?.total_validators}` },
              { l: 'Avg APY', v: `${dashboard.network?.avg_apy}%` },
              { l: 'Avg Commission', v: `${dashboard.network?.avg_commission}%` },
              { l: 'Delegators', v: dashboard.network?.total_delegators },
              { l: 'Rewards Paid', v: fmt(dashboard.network?.total_rewards_distributed || 0) },
              { l: 'Epoch', v: dashboard.network?.current_epoch },
            ].map(s => (
              <div key={s.l} style={{ ...panel, flex: '1 1 100px', textAlign: 'center' }}>
                <div style={{ fontSize: '10px', color: '#888' }}>{s.l}</div>
                <div style={{ fontSize: '16px', fontWeight: 700 }}>{s.v}</div>
              </div>
            ))}
          </div>

          {/* User Summary */}
          {dashboard.user && (
            <div style={panel}>
              <div style={{ fontSize: '14px', fontWeight: 600, marginBottom: '8px' }}>Your Staking</div>
              <div style={{ display: 'flex', gap: '16px', fontSize: '12px', color: '#888', flexWrap: 'wrap' }}>
                <span>Staked: <b style={{ color: '#4F46E5' }}>{fmt(dashboard.user.total_staked || 0)} VRS</b></span>
                <span>Positions: <b>{dashboard.user.active_positions}/{dashboard.user.total_positions}</b></span>
                <span>Pending: <b style={{ color: '#22C55E' }}>{fmt(dashboard.user.pending_rewards || 0)} VRS</b></span>
                <span>Claimed: <b>{fmt(dashboard.user.rewards?.total_claimed || 0)}</b></span>
                <span>Compounded: <b>{fmt(dashboard.user.rewards?.total_compounded || 0)}</b></span>
              </div>
            </div>
          )}

          {/* Top Validators */}
          <div style={panel}>
            <div style={{ fontSize: '13px', fontWeight: 600, marginBottom: '8px' }}>Top Validators</div>
            {dashboard.top_validators?.map((v, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', borderBottom: '1px solid #222' }}>
                <div style={{ fontSize: '12px' }}>{v.name}</div>
                <div style={{ display: 'flex', gap: '12px', fontSize: '11px' }}>
                  <span style={{ color: '#888' }}>⬇ {fmt(v.total_staked)}</span>
                  <span style={{ color: '#4F46E5' }}>APY {v.apy}%</span>
                  <span style={{ color: gradeColor[v.grade] || '#888' }}>{v.grade}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {tab === 'validators' && (
        <div style={{ display: 'grid', gap: '6px' }}>
          {validators.map((v, i) => (
            <div key={i} style={panel}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <div style={{ fontSize: '13px', fontWeight: 600 }}>{v.name}</div>
                <span style={{ fontSize: '9px', padding: '2px 6px', borderRadius: '4px', background: (gradeColor[v.grade] || '#888') + '22', color: gradeColor[v.grade] || '#888' }}>Grade {v.grade}</span>
              </div>
              <div style={{ display: 'flex', gap: '12px', fontSize: '11px', marginTop: '4px', color: '#888', flexWrap: 'wrap' }}>
                <span>Staked: {fmt(v.total_staked)}</span>
                <span>Delegators: {v.delegator_count}</span>
                <span>Commission: {v.commission_rate}%</span>
                <span style={{ color: '#4F46E5' }}>APY: {v.apy}%</span>
                <span>Green: {v.green_score}</span>
                <span>Self-stake: {fmt(v.self_stake)}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {tab === 'positions' && (
        <div style={{ display: 'grid', gap: '12px' }}>
          <div style={{ ...panel, maxWidth: '500px' }}>
            <div style={{ fontSize: '14px', fontWeight: 600, marginBottom: '12px' }}>Stake Tokens</div>
            <div style={{ display: 'grid', gap: '8px' }}>
              <select value={stakeForm.validator_id} onChange={e => setStakeForm({ ...stakeForm, validator_id: e.target.value })} style={input}>
                {validators.map(v => <option key={v.validator_id} value={v.validator_id}>{v.name} (APY {v.apy}%)</option>)}
              </select>
              <input type="number" value={stakeForm.amount} onChange={e => setStakeForm({ ...stakeForm, amount: parseFloat(e.target.value) })} placeholder="Amount" style={input} />
              <label style={{ fontSize: '12px', color: '#888', display: 'flex', alignItems: 'center', gap: '4px' }}>
                <input type="checkbox" checked={stakeForm.auto_compound} onChange={e => setStakeForm({ ...stakeForm, auto_compound: e.target.checked })} /> Auto-compound rewards
              </label>
              <button onClick={handleStake} style={{ ...btn, background: '#4F46E5' }}>Stake</button>
            </div>
          </div>

          {positions.map((p, i) => (
            <div key={i} style={panel}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <div style={{ fontSize: '13px', fontWeight: 600 }}>{p.validator_name}</div>
                <span style={{ fontSize: '9px', padding: '2px 6px', borderRadius: '4px', background: (statusColor[p.status] || '#888') + '22', color: statusColor[p.status] || '#888' }}>{p.status}</span>
              </div>
              <div style={{ display: 'flex', gap: '12px', fontSize: '11px', marginTop: '4px', color: '#888', flexWrap: 'wrap' }}>
                <span>Amount: <b style={{ color: '#4F46E5' }}>{fmt(p.amount)} VRS</b></span>
                <span>APY: {p.apy}%</span>
                <span>Earned: {fmt(p.rewards_earned)}</span>
                {p.auto_compound && <span style={{ color: '#22C55E' }}>Auto-compound</span>}
              </div>
              {p.status === 'active' && (
                <div style={{ display: 'flex', gap: '8px', marginTop: '8px' }}>
                  <button onClick={() => handleClaim(p.id)} style={{ ...btn, background: '#22C55E', fontSize: '11px', padding: '4px 12px' }}>Claim Rewards</button>
                  <button onClick={() => handleCompound(p.id)} style={{ ...btn, background: '#4F46E5', fontSize: '11px', padding: '4px 12px' }}>Compound</button>
                  <button onClick={() => handleUnstake(p.id)} style={{ ...btn, background: '#EF4444', fontSize: '11px', padding: '4px 12px' }}>Unstake</button>
                </div>
              )}
            </div>
          ))}
          {positions.length === 0 && <div style={{ fontSize: '12px', color: '#888', textAlign: 'center', padding: '20px' }}>No staking positions yet</div>}
        </div>
      )}

      {tab === 'calculator' && (
        <div style={{ display: 'grid', gap: '12px' }}>
          <div style={{ ...panel, maxWidth: '500px' }}>
            <div style={{ fontSize: '14px', fontWeight: 600, marginBottom: '12px' }}>Staking Calculator</div>
            <div style={{ display: 'grid', gap: '8px' }}>
              <div style={{ display: 'flex', gap: '8px' }}>
                <input type="number" value={calcInput.amount} onChange={e => setCalcInput({ ...calcInput, amount: parseFloat(e.target.value) })} placeholder="Amount" style={input} />
                <input type="number" value={calcInput.apy} onChange={e => setCalcInput({ ...calcInput, apy: parseFloat(e.target.value) })} placeholder="APY %" style={input} />
              </div>
              <div style={{ display: 'flex', gap: '8px' }}>
                <input type="number" value={calcInput.days} onChange={e => setCalcInput({ ...calcInput, days: parseInt(e.target.value) })} placeholder="Days" style={input} />
                <label style={{ fontSize: '12px', color: '#888', display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <input type="checkbox" checked={calcInput.compound} onChange={e => setCalcInput({ ...calcInput, compound: e.target.checked })} /> Compound
                </label>
              </div>
              <button onClick={handleCalculate} style={{ ...btn, background: '#4F46E5' }}>Calculate</button>
            </div>
          </div>

          {calcResult && (
            <div style={{ ...panel, maxWidth: '500px' }}>
              <div style={{ fontSize: '14px', fontWeight: 600, marginBottom: '8px' }}>Projection Results</div>
              <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
                {[{ l: 'Principal', v: fmt(calcResult.principal) }, { l: 'Projected Rewards', v: fmt(calcResult.projected_rewards) }, { l: 'Total Value', v: fmt(calcResult.projected_total) }, { l: 'Daily Rewards', v: fmt(calcResult.daily_rewards) }].map(s => (
                  <div key={s.l} style={{ ...panel, flex: '1 1 100px', textAlign: 'center' }}>
                    <div style={{ fontSize: '10px', color: '#888' }}>{s.l}</div>
                    <div style={{ fontSize: '15px', fontWeight: 700, color: s.l.includes('Rewards') ? '#22C55E' : '#fff' }}>{s.v}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default StakingDashboard;
