import React, { useState, useEffect, useCallback } from 'react';
import crossChainService from '../services/crossChainService';

function CrossChainAnalytics() {
  const [tab, setTab] = useState('overview');
  const [dashboard, setDashboard] = useState(null);
  const [transfers, setTransfers] = useState([]);
  const [chainFilter, setChainFilter] = useState('');
  const [autoRefresh, setAutoRefresh] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const [dash, txfrs] = await Promise.all([
        crossChainService.dashboard(),
        crossChainService.transfers({ limit: 50, sort_by: 'timestamp' }),
      ]);
      setDashboard(dash.data || null);
      setTransfers(txfrs.data || []);
    } catch (err) { console.error(err); }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);
  useEffect(() => {
    if (!autoRefresh) return;
    const i = setInterval(fetchData, 10000);
    return () => clearInterval(i);
  }, [autoRefresh, fetchData]);

  const fmt = (n) => n >= 1e9 ? `${(n/1e9).toFixed(2)}B` : n >= 1e6 ? `${(n/1e6).toFixed(2)}M` : n >= 1e3 ? `${(n/1e3).toFixed(1)}K` : n.toFixed(2);
  const chainColor = { ethereum: '#627EEA', verdis: '#22C55E', bsc: '#F0B90B', polygon: '#8247E5', avalanche: '#E84142', arbitrum: '#28A0F0', optimism: '#FF0420', solana: '#14F195' };
  const panel = { background: '#1A1A1E', borderRadius: '10px', border: '1px solid #333', padding: '14px' };
  const btn = { padding: '8px 16px', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '13px', color: '#fff' };

  const filtered = chainFilter ? transfers.filter(t => t.source_chain === chainFilter || t.target_chain === chainFilter) : transfers;

  return (
    <div style={{ padding: '24px' }}>
      <h1 style={{ fontSize: '28px', fontWeight: 700, marginBottom: '4px''>🌍 Cross-Chain Analytics</h1>
      <p style={{ color: '#888', marginBottom: '12px' }}>Multi-chain transfer tracking and flow analysis</p>

      <div style={{ display: 'flex', gap: '4px', marginBottom: '12px' }}>
        {['overview', 'transfers', 'corridors'].map(t => (
          <button key={t} onClick={() => setTab(t)} style={{ ...btn, background: tab === t ? '#4F46E5' : '#1A1A1E', textTransform: 'capitalize' }}>{t}</button>
        ))}
        <button onClick={() => setAutoRefresh(!autoRefresh)} style={{ ...btn, background: autoRefresh ? '#22C55E' : '#1A1A1E' }}>{autoRefresh ? '⏸ Auto' : '▶ Auto'}</button>
      </div>

      {tab === 'overview' && dashboard && (
        <div style={{ display: 'grid', gap: '12px' }}>
          {/* Stats */}
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            {[
              { l: 'Total Transfers', v: dashboard.stats?.total_transfers || 0 },
              { l: 'Total Volume', v: fmt(dashboard.stats?.total_volume || 0) },
              { l: 'Success Rate', v: `${dashboard.stats?.success_rate}%` },
              { l: 'Chains', v: dashboard.stats?.total_chains },
              { l: 'Corridors', v: dashboard.stats?.active_corridors },
              { l: 'Bridges', v: dashboard.stats?.bridges_used },
              { l: 'Tokens', v: dashboard.stats?.tokens_transferred },
              { l: 'Avg Duration', v: `${dashboard.stats?.avg_duration}s` },
            ].map(s => (
              <div key={s.l} style={{ ...panel, flex: '1 1 100px', textAlign: 'center' }}>
                <div style={{ fontSize: '10px', color: '#888' }}>{s.l}</div>
                <div style={{ fontSize: '16px', fontWeight: 700 }}>{s.v}</div>
              </div>
            ))}
          </div>

          {/* Flow Analysis */}
          <div style={panel}>
            <div style={{ fontSize: '14px', fontWeight: 600, marginBottom: '8px' }}>24h Flow Analysis</div>
            <div style={{ fontSize: '11px', color: '#888', marginBottom: '8px' }}>
              <span>Transfers: <b style={{ color: '#fff' }}>{dashboard.flow_24h?.total_transfers}</b></span>
              <span style={{ marginLeft: '16px' }}>Volume: <b style={{ color: '#4F46E5' }}>{fmt(dashboard.flow_24h?.total_volume || 0)}</b></span>
              <span style={{ marginLeft: '16px' }}>Avg Size: <b style={{ color: '#fff' }}>{fmt(dashboard.flow_24h?.avg_transfer_size || 0)}</b></span>
            </div>
            {/* Net flows */}
            <div style={{ display: 'grid', gap: '4px' }}>
              {Object.entries(dashboard.flow_24h?.net_flows || {}).filter(([_, v]) => v !== 0).slice(0, 8).map(([chain, flow]) => (
                <div key={chain} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px' }}>
                  <span style={{ textTransform: 'capitalize' }}>{chain}</span>
                  <span style={{ color: flow > 0 ? '#22C55E' : '#EF4444' }}>{flow > 0 ? '+' : ''}{fmt(flow)}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Volume Trend */}
          <div style={panel}>
            <div style={{ fontSize: '14px', fontWeight: 600, marginBottom: '8px' }}>7-Day Volume Trend</div>
            <div style={{ display: 'flex', gap: '4px', alignItems: 'flex-end', height: '60px' }}>
              {dashboard.volume_trend?.map((d, i) => {
                const maxVol = Math.max(...(dashboard.volume_trend || []).map(v => v.volume), 1);
                const h = Math.max(4, (d.volume / maxVol) * 50);
                return <div key={i} style={{ flex: 1, textAlign: 'center' }}>
                  <div style={{ height: `${h}px`, background: '#4F46E5', borderRadius: '3px 3px 0 0' }} />
                  <div style={{ fontSize: '8px', color: '#666', marginTop: '2px' }}>{d.date.slice(5)}</div>
                </div>;
              })}
            </div>
          </div>

          {/* Chain Comparison */}
          <div style={panel}>
            <div style={{ fontSize: '14px', fontWeight: 600, marginBottom: '8px' }}>Chain Comparison</div>
            {dashboard.chain_comparison?.map((c, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', borderBottom: '1px solid #222', fontSize: '12px' }}>
                <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                  <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: chainColor[c.chain] || '#888' }} />
                  <span style={{ textTransform: 'capitalize' }}>{c.chain}</span>
                </div>
                <div style={{ display: 'flex', gap: '12px', fontSize: '10px', color: '#888' }}>
                  <span>Transfers: {c.total_transfers}</span>
                  <span>Vol: {fmt(c.total_volume)}</span>
                  <span style={{ color: c.net_flow > 0 ? '#22C55E' : '#EF4444' }}>Net: {fmt(c.net_flow)}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {tab === 'transfers' && (
        <div style={{ display: 'grid', gap: '6px' }}>
          <select value={chainFilter} onChange={e => setChainFilter(e.target.value)} style={{ padding: '8px 12px', background: '#0D0D0F', border: '1px solid #333', borderRadius: '6px', color: '#fff', fontSize: '13px', maxWidth: '200px' }}>
            <option value="">All chains</option>
            {['ethereum', 'verdis', 'bsc', 'polygon', 'avalanche', 'arbitrum', 'optimism', 'solana'].map(c => <option key={c} value={c}>{c}</option>)}
          </select>
          {filtered.slice(0, 30).map((t, i) => (
            <div key={i} style={panel}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <div style={{ display: 'flex', gap: '8px', alignItems: 'center', fontSize: '12px' }}>
                  <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: chainColor[t.source_chain] || '#888' }} />
                  <span style={{ textTransform: 'capitalize' }}>{t.source_chain}</span>
                  <span style={{ color: '#4F46E5' }}>→</span>
                  <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: chainColor[t.target_chain] || '#888' }} />
                  <span style={{ textTransform: 'capitalize' }}>{t.target_chain}</span>
                </div>
                <span style={{ fontSize: '10px', padding: '2px 6px', borderRadius: '4px', background: t.status === 'confirmed' ? '#22C55E22' : t.status === 'pending' ? '#FFA50022' : '#EF444422', color: t.status === 'confirmed' ? '#22C55E' : t.status === 'pending' ? '#FFA500' : '#EF4444' }}>{t.status}</span>
              </div>
              <div style={{ display: 'flex', gap: '12px', fontSize: '11px', marginTop: '4px', color: '#888', flexWrap: 'wrap' }}>
                <span>{t.token}: <b style={{ color: '#fff' }}>{fmt(t.amount)}</b></span>
                <span>Bridge: {t.bridge_protocol}</span>
                <span>Duration: {t.duration_seconds}s</span>
                <span>Gas: {t.gas_paid}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {tab === 'corridors' && dashboard && (
        <div style={{ display: 'grid', gap: '6px' }}>
          {dashboard.top_corridors?.map((c, i) => (
            <div key={i} style={panel}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <div style={{ fontSize: '13px', fontWeight: 600 }}>
                  <span style={{ textTransform: 'capitalize' }}>{c.source_chain}</span>
                  <span style={{ color: '#4F46E5', margin: '0 4px' }}>→</span>
                  <span style={{ textTransform: 'capitalize' }}>{c.target_chain}</span>
                </div>
                <span style={{ fontSize: '11px', color: '#888' }}>{c.transfer_count} transfers</span>
              </div>
              <div style={{ display: 'flex', gap: '12px', fontSize: '11px', marginTop: '4px', color: '#888' }}>
                <span>Volume: <b style={{ color: '#4F46E5' }}>{fmt(c.total_volume)}</b></span>
                <span>Avg: {fmt(c.avg_transfer_size)}</span>
                {Object.entries(c.token_breakdown || {}).slice(0, 3).map(([token, vol]) => <span key={token}>{token}: {fmt(vol)}</span>)}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default CrossChainAnalytics;
