import React, { useState, useEffect, useCallback } from 'react';
import faucetService from '../services/faucetService';

function Faucet() {
  const [tab, setTab] = useState('claim');
  const [dashboard, setDashboard] = useState(null);
  const [stats, setStats] = useState(null);
  const [captcha, setCaptcha] = useState(null);
  const [captchaAnswer, setCaptchaAnswer] = useState('');
  const [walletAddress, setWalletAddress] = useState('');
  const [claimResult, setClaimResult] = useState(null);
  const [autoRefresh, setAutoRefresh] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const [dash, st] = await Promise.all([faucetService.dashboard(), faucetService.stats()]);
      setDashboard(dash.data || null);
      setStats(st.data || null);
    } catch (err) { console.error(err); }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);
  useEffect(() => {
    if (!autoRefresh) return;
    const i = setInterval(fetchData, 15000);
    return () => clearInterval(i);
  }, [autoRefresh, fetchData]);

  const handleGetCaptcha = async () => {
    try {
      const r = await faucetService.captcha();
      setCaptcha(r.data);
      setCaptchaAnswer('');
      setClaimResult(null);
    } catch (e) { console.error(e); }
  };

  const handleClaim = async () => {
    if (!walletAddress) return;
    try {
      const r = await faucetService.claim({
        address: walletAddress,
        captcha_id: captcha?.challenge_id || '',
        captcha_answer: captchaAnswer,
      });
      setClaimResult(r.data);
      fetchData();
    } catch (e) { setClaimResult({ error: e.message }); }
  };

  const fmt = (n) => n >= 1e9 ? `${(n/1e9).toFixed(2)}B` : n >= 1e6 ? `${(n/1e6).toFixed(2)}M` : n >= 1e3 ? `${(n/1e3).toFixed(1)}K` : n.toFixed(2);
  const statusColor = { active: '#22C55E', paused: '#FFA500', depleted: '#EF4444' };
  const reqStatusColor = { pending: '#FFA500', approved: '#4F46E5', distributed: '#22C55E', failed: '#EF4444', rejected: '#EF4444' };
  const panel = { background: '#1A1A1E', borderRadius: '10px', border: '1px solid #333', padding: '14px' };
  const btn = { padding: '8px 16px', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '13px', color: '#fff' };
  const input = { padding: '8px 12px', background: '#0D0D0F', border: '1px solid #333', borderRadius: '6px', color: '#fff', fontSize: '13px', width: '100%' };

  return (
    <div style={{ padding: '24px' }}>
      <h1 style={{ fontSize: '28px', fontWeight: 700, marginBottom: '4px' }}>🚰 Faucet</h1>
      <p style={{ color: '#888', marginBottom: '12px' }}>Get testnet VRS tokens for development and testing</p>

      <div style={{ display: 'flex', gap: '4px', marginBottom: '12px' }}>
        {['claim', 'stats', 'requests'].map(t => (
          <button key={t} onClick={() => setTab(t)} style={{ ...btn, background: tab === t ? '#4F46E5' : '#1A1A1E', textTransform: 'capitalize' }}>{t}</button>
        ))}
        <button onClick={() => setAutoRefresh(!autoRefresh)} style={{ ...btn, background: autoRefresh ? '#22C55E' : '#1A1A1E' }}>{autoRefresh ? '⏸ Auto' : '▶ Auto'}</button>
      </div>

      {tab === 'claim' && (
        <div style={{ display: 'grid', gap: '12px', maxWidth: '500px' }}>
          <div style={panel}>
            <div style={{ fontSize: '14px', fontWeight: 600, marginBottom: '12px' }}>Request Testnet Tokens</div>
            {stats && (
              <div style={{ fontSize: '12px', color: '#888', marginBottom: '12px' }}>
                <span style={{ color: statusColor[stats.status] || '#888' }}>● {stats.status}</span>
                {' | '}Drip: <b style={{ color: '#4F46E5' }}>{fmt(stats.drip_amount)} VRS</b>
                {' | '}Cooldown: <b>{stats.cooldown_hours}h</b>
                {' | '}Remaining: <b>{fmt(stats.remaining)} VRS</b>
              </div>
            )}
            <div style={{ display: 'grid', gap: '8px' }}>
              <input value={walletAddress} onChange={e => setWalletAddress(e.target.value)} placeholder="Wallet address (0x...)" style={input} />
              {captcha && (
                <div>
                  <div style={{ fontSize: '12px', color: '#888', marginBottom: '4px' }}>{captcha.question}</div>
                  <input value={captchaAnswer} onChange={e => setCaptchaAnswer(e.target.value)} placeholder="Answer" style={input} />
                </div>
              )}
              <div style={{ display: 'flex', gap: '8px' }}>
                <button onClick={handleGetCaptcha} style={{ ...btn, background: '#1A1A1E' }}>Get Captcha</button>
                <button onClick={handleClaim} style={{ ...btn, background: '#4F46E5' }}>Claim Tokens</button>
              </div>
            </div>
            {claimResult && (
              <div style={{ marginTop: '12px', padding: '10px', background: '#0D0D0F', borderRadius: '6px', fontSize: '12px' }}>
                {claimResult.error ? (
                  <div style={{ color: '#EF4444' }}>❌ {claimResult.error}</div>
                ) : (
                  <div>
                    <div style={{ color: '#22C55E', marginBottom: '4px' }}>✅ Distributed {fmt(claimResult.amount)} VRS!</div>
                    <div style={{ color: '#888' }}>TX: <code style={{ color: '#4F46E5' }}>{claimResult.tx_hash?.slice(0, 20)}...</code></div>
                    <div style={{ color: '#888' }}>Remaining supply: {fmt(claimResult.remaining_supply)} VRS</div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {tab === 'stats' && stats && (
        <div style={{ display: 'grid', gap: '12px' }}>
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            {[
              { l: 'Status', v: stats.status, c: statusColor[stats.status] },
              { l: 'Total Supply', v: fmt(stats.total_supply) },
              { l: 'Distributed', v: fmt(stats.distributed) },
              { l: 'Remaining', v: fmt(stats.remaining) },
              { l: 'Remaining %', v: `${stats.remaining_percentage}%` },
              { l: 'Total Requests', v: stats.total_requests },
              { l: 'Distributed', v: stats.distributed_count },
              { l: 'Unique Addresses', v: stats.unique_addresses },
              { l: 'Today', v: fmt(stats.today_distributed) },
              { l: 'Daily Limit', v: fmt(stats.daily_limit) },
            ].map(s => (
              <div key={s.l} style={{ ...panel, flex: '1 1 100px', textAlign: 'center' }}>
                <div style={{ fontSize: '10px', color: '#888' }}>{s.l}</div>
                <div style={{ fontSize: '16px', fontWeight: 700, color: s.c || '#fff' }}>{s.v}</div>
              </div>
            ))}
          </div>

          {dashboard && (
            <div style={panel}>
              <div style={{ fontSize: '14px', fontWeight: 600, marginBottom: '8px' }}>Top Claimers</div>
              {dashboard.top_claimers?.map((c, i) => (
                <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', borderBottom: '1px solid #222', fontSize: '12px' }}>
                  <span>{c.address.slice(0, 12)}...</span>
                  <div style={{ display: 'flex', gap: '12px' }}>
                    <span style={{ color: '#4F46E5' }}>{fmt(c.total)} VRS</span>
                    <span style={{ color: '#888' }}>{c.claims} claims</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {tab === 'requests' && dashboard && (
        <div style={{ display: 'grid', gap: '6px' }}>
          {dashboard.recent_requests?.map((r, i) => (
            <div key={i} style={panel}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <div style={{ fontSize: '12px' }}>{r.address.slice(0, 14)}...</div>
                <span style={{ fontSize: '9px', padding: '2px 6px', borderRadius: '4px', background: (reqStatusColor[r.status] || '#888') + '22', color: reqStatusColor[r.status] || '#888' }}>{r.status}</span>
              </div>
              <div style={{ display: 'flex', gap: '12px', fontSize: '10px', marginTop: '4px', color: '#888', flexWrap: 'wrap' }}>
                <span>Amount: <b style={{ color: '#4F46E5' }}>{fmt(r.amount)} VRS</b></span>
                {r.tx_hash && <span>TX: {r.tx_hash.slice(0, 16)}...</span>}
                <span>IP: {r.ip_address}</span>
                <span>{new Date(r.created).toLocaleString()}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default Faucet;
