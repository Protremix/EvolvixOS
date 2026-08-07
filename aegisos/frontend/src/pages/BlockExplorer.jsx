import React, { useState, useEffect, useCallback } from 'react';
import explorerService from '../services/explorerService';

function BlockExplorer() {
  const [tab, setTab] = useState('overview');
  const [dashboard, setDashboard] = useState(null);
  const [blocks, setBlocks] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [contracts, setContracts] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResult, setSearchResult] = useState(null);
  const [autoRefresh, setAutoRefresh] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const [dash, blks, txs, ctrs] = await Promise.all([
        explorerService.dashboard(),
        explorerService.latestBlocks(20),
        explorerService.transactions({ limit: 20 }),
        explorerService.contracts({ limit: 10 }),
      ]);
      setDashboard(dash.data || null);
      setBlocks(blks.data || []);
      setTransactions(txs.data || []);
      setContracts(ctrs.data || []);
    } catch (err) { console.error(err); }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);
  useEffect(() => {
    if (!autoRefresh) return;
    const i = setInterval(fetchData, 10000);
    return () => clearInterval(i);
  }, [autoRefresh, fetchData]);

  const handleSearch = async () => {
    if (!searchQuery) return;
    try {
      const r = await explorerService.search(searchQuery);
      setSearchResult(r.data);
    } catch (e) { console.error(e); }
  };

  const fmt = (n) => n >= 1e9 ? `${(n/1e9).toFixed(2)}B` : n >= 1e6 ? `${(n/1e6).toFixed(2)}M` : n >= 1e3 ? `${(n/1e3).toFixed(1)}K` : n.toFixed(2);
  const statusColor = { success: '#22C55E', failed: '#EF4444', pending: '#FFA500' };
  const typeColor = { transfer: '#4F46E5', stake: '#22C55E', unstake: '#FFA500', reward: '#A855F7', slash: '#EF4444', contract_call: '#06B6D4', contract_deploy: '#10B981', governance: '#F59E0B', bridge: '#8B5CF6', nft_mint: '#EC4899', nft_transfer: '#F472B6', validator: '#3B82F6' };
  const panel = { background: '#1A1A1E', borderRadius: '10px', border: '1px solid #333', padding: '14px' };
  const btn = { padding: '8px 16px', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '13px', color: '#fff' };
  const input = { padding: '8px 12px', background: '#0D0D0F', border: '1px solid #333', borderRadius: '6px', color: '#fff', fontSize: '13px', width: '100%' };

  return (
    <div style={{ padding: '24px' }}>
      <h1 style={{ fontSize: '28px', fontWeight: 700, marginBottom: '4px' }}>🔍 Block Explorer</h1>
      <p style={{ color: '#888', marginBottom: '12px' }}>Verdis blockchain data — blocks, transactions, addresses, contracts</p>

      {/* Search bar */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '12px' }}>
        <input value={searchQuery} onChange={e => setSearchQuery(e.target.value)} placeholder="Search by block height, tx hash, or address (0x...)" style={input} onKeyDown={e => e.key === 'Enter' && handleSearch()} />
        <button onClick={handleSearch} style={{ ...btn, background: '#4F46E5' }}>Search</button>
      </div>

      {searchResult && (
        <div style={{ ...panel, marginBottom: '12px' }}>
          <div style={{ fontSize: '12px', color: '#888' }}>Search result type: <b style={{ color: '#4F46E5' }}>{searchResult.type}</b></div>
          {searchResult.data ? (
            <pre style={{ fontSize: '11px', color: '#aaa', marginTop: '8px', maxHeight: '200px', overflow: 'auto' }}>{JSON.stringify(searchResult.data, null, 2)}</pre>
          ) : (
            <div style={{ fontSize: '12px', color: '#EF4444', marginTop: '4px' }}>{searchResult.error || 'No results'}</div>
          )}
        </div>
      )}

      <div style={{ display: 'flex', gap: '4px', marginBottom: '12px', flexWrap: 'wrap' }}>
        {['overview', 'blocks', 'transactions', 'contracts'].map(t => (
          <button key={t} onClick={() => setTab(t)} style={{ ...btn, background: tab === t ? '#4F46E5' : '#1A1A1E', textTransform: 'capitalize' }}>{t}</button>
        ))}
        <button onClick={() => setAutoRefresh(!autoRefresh)} style={{ ...btn, background: autoRefresh ? '#22C55E' : '#1A1A1E' }}>{autoRefresh ? '⏸ Auto' : '▶ Auto'}</button>
      </div>

      {tab === 'overview' && dashboard && (
        <div style={{ display: 'grid', gap: '12px' }}>
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            {[
              { l: 'Block Height', v: dashboard.network_stats?.current_height || 0 },
              { l: 'Total Blocks', v: fmt(dashboard.network_stats?.total_blocks || 0) },
              { l: 'Total Txs', v: fmt(dashboard.network_stats?.total_transactions || 0) },
              { l: 'Success Rate', v: `${dashboard.network_stats?.success_rate || 0}%` },
              { l: 'Addresses', v: fmt(dashboard.network_stats?.total_addresses || 0) },
              { l: 'Contracts', v: dashboard.network_stats?.total_contracts || 0 },
              { l: 'TPS', v: dashboard.network_stats?.tps || 0 },
              { l: 'Block Time', v: `${dashboard.network_stats?.block_time || 6}s` },
            ].map(s => (
              <div key={s.l} style={{ ...panel, flex: '1 1 100px', textAlign: 'center' }}>
                <div style={{ fontSize: '10px', color: '#888' }}>{s.l}</div>
                <div style={{ fontSize: '16px', fontWeight: 700 }}>{s.v}</div>
              </div>
            ))}
          </div>

          {/* Latest Blocks */}
          <div style={panel}>
            <div style={{ fontSize: '14px', fontWeight: 600, marginBottom: '8px' }}>Latest Blocks</div>
            {dashboard.latest_blocks?.map((b, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', borderBottom: '1px solid #222', fontSize: '12px' }}>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <span style={{ color: '#4F46E5' }}>#{b.height}</span>
                  <span style={{ color: '#888' }}>{b.tx_count} txs</span>
                </div>
                <div style={{ display: 'flex', gap: '8px', fontSize: '10px', color: '#888' }}>
                  <span>Gas: {fmt(b.gas_used)}</span>
                  <span>{b.proposer?.slice(0, 10)}...</span>
                  <span>{new Date(b.timestamp).toLocaleTimeString()}</span>
                </div>
              </div>
            ))}
          </div>

          {/* Latest Transactions */}
          <div style={panel}>
            <div style={{ fontSize: '14px', fontWeight: 600, marginBottom: '8px' }}>Latest Transactions</div>
            {dashboard.latest_transactions?.map((t, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', borderBottom: '1px solid #222', fontSize: '12px' }}>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <span style={{ fontSize: '9px', padding: '1px 4px', borderRadius: '3px', background: (typeColor[t.tx_type] || '#888') + '22', color: typeColor[t.tx_type] || '#888' }}>{t.tx_type}</span>
                  <span style={{ color: '#888' }}>{t.hash?.slice(0, 16)}...</span>
                </div>
                <div style={{ display: 'flex', gap: '8px', fontSize: '10px' }}>
                  <span style={{ color: statusColor[t.status] || '#888' }}>●</span>
                  <span style={{ color: '#4F46E5' }}>{fmt(t.value)}</span>
                  <span style={{ color: '#888' }}>{t.from_address?.slice(0, 8)}...</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {tab === 'blocks' && (
        <div style={{ display: 'grid', gap: '4px' }}>
          {blocks.map((b, i) => (
            <div key={i} style={panel}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <div style={{ fontSize: '13px', fontWeight: 600', color: '#4F46E5' }}>Block #{b.height}</div>
                <span style={{ fontSize: '10px', color: '#888' }}>{new Date(b.timestamp).toLocaleString()}</span>
              </div>
              <div style={{ display: 'flex', gap: '12px', fontSize: '11px', marginTop: '4px', color: '#888', flexWrap: 'wrap' }}>
                <span>Txs: <b>{b.tx_count}</b></span>
                <span>Gas: {fmt(b.gas_used)}/{fmt(b.gas_limit)}</span>
                <span>Size: {fmt(b.size)} bytes</span>
                <span>Validator: {b.validator?.slice(0, 12)}...</span>
                <span>Epoch: {b.epoch}</span>
                <span>Hash: {b.hash?.slice(0, 20)}...</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {tab === 'transactions' && (
        <div style={{ display: 'grid', gap: '4px' }}>
          {transactions.map((t, i) => (
            <div key={i} style={panel}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                  <span style={{ fontSize: '9px', padding: '2px 6px', borderRadius: '4px', background: (typeColor[t.tx_type] || '#888') + '22', color: typeColor[t.tx_type] || '#888' }}>{t.tx_type}</span>
                  <span style={{ fontSize: '12px', color: '#4F46E5' }}>{t.hash?.slice(0, 18)}...</span>
                </div>
                <span style={{ fontSize: '9px', padding: '2px 6px', borderRadius: '4px', background: (statusColor[t.status] || '#888') + '22', color: statusColor[t.status] || '#888' }}>{t.status}</span>
              </div>
              <div style={{ display: 'flex', gap: '12px', fontSize: '11px', marginTop: '4px', color: '#888', flexWrap: 'wrap' }}>
                <span>From: {t.from_address?.slice(0, 12)}...</span>
                <span>To: {t.to_address?.slice(0, 12)}...</span>
                <span>Value: <b style={{ color: '#4F46E5' }}>{fmt(t.value)} VRS</b></span>
                <span>Gas: {fmt(t.gas_used)}</span>
                <span>Block: #{t.block_height}</span>
                <span>Fee: {t.fee}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {tab === 'contracts' && (
        <div style={{ display: 'grid', gap: '6px' }}>
          {contracts.map((c, i) => (
            <div key={i} style={panel}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <div style={{ fontSize: '13px', fontWeight: 600 }}>{c.name}</div>
                <div style={{ display: 'flex', gap: '4px' }}>
                  {c.standard && <span style={{ fontSize: '9px', padding: '2px 6px', borderRadius: '4px', background: '#4F46E522', color: '#4F46E5' }}>{c.standard}</span>}
                  {c.verified && <span style={{ fontSize: '9px', padding: '2px 6px', borderRadius: '4px', background: '#22C55E22', color: '#22C55E' }}>✓ verified</span>}
                </div>
              </div>
              <div style={{ display: 'flex', gap: '12px', fontSize: '11px', marginTop: '4px', color: '#888', flexWrap: 'wrap' }}>
                <span>Address: {c.address?.slice(0, 14)}...</span>
                <span>Creator: {c.creator?.slice(0, 12)}...</span>
                <span>Calls: {c.calls}</span>
                <span>Created: {new Date(c.created_at).toLocaleDateString()}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default BlockExplorer;
