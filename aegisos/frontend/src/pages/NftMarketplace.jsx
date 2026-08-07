import React, { useState, useEffect, useCallback } from 'react';
import nftService from '../services/nftService';

function NftMarketplace() {
  const [tab, setTab] = useState('explore');
  const [dashboard, setDashboard] = useState(null);
  const [collections, setCollections] = useState([]);
  const [listings, setListings] = useState([]);
  const [nfts, setNfts] = useState([]);
  const [autoRefresh, setAutoRefresh] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const [dash, cols, lsts, ns] = await Promise.all([
        nftService.dashboard(),
        nftService.collections({ sort_by: 'total_volume' }),
        nftService.listings({ status: 'active', sort_by: 'price' }),
        nftService.nfts({ listed: true, limit: 50 }),
      ]);
      setDashboard(dash.data || null);
      setCollections(cols.data || []);
      setListings(lsts.data || []);
      setNfts(ns.data || []);
    } catch (err) { console.error(err); }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);
  useEffect(() => {
    if (!autoRefresh) return;
    const i = setInterval(fetchData, 10000);
    return () => clearInterval(i);
  }, [autoRefresh, fetchData]);

  const handleBuy = async (listingId) => {
    try { await nftService.buyNft(listingId, '0xverdis'); fetchData(); } catch (e) { console.error(e); }
  };

  const fmt = (n) => n >= 1e9 ? `${(n/1e9).toFixed(2)}B` : n >= 1e6 ? `${(n/1e6).toFixed(2)}M` : n >= 1e3 ? `${(n/1e3).toFixed(1)}K` : n.toFixed(2);
  const typeColor = { carbon_credit: '#22C55E', reforestation: '#10B981', green_validator: '#4F46E5', art: '#FF6B6B', gaming: '#FFA500', music: '#A855F7', domain: '#06B6D4', utility: '#F59E0B', collectible: '#888' };
  const rarityColor = { common: '#888', uncommon: '#22C55E', rare: '#4F46E5', epic: '#A855F7', legendary: '#FFA500' };
  const statusColor = { active: '#22C55E', sold: '#4F46E5', cancelled: '#888', expired: '#EF4444' };
  const panel = { background: '#1A1A1E', borderRadius: '10px', border: '1px solid #333', padding: '14px' };
  const btn = { padding: '8px 16px', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '13px', color: '#fff' };

  return (
    <div style={{ padding: '24px' }}>
      <h1 style={{ fontSize: '28px', fontWeight: 700, marginBottom: '4px' }}>🎨 NFT Marketplace</h1>
      <p style={{ color: '#888', marginBottom: '12px' }}>Mint, trade, and collect NFTs including carbon credits and reforestation tokens</p>

      <div style={{ display: 'flex', gap: '4px', marginBottom: '12px', flexWrap: 'wrap' }}>
        {['explore', 'collections', 'listings'].map(t => (
          <button key={t} onClick={() => setTab(t)} style={{ ...btn, background: tab === t ? '#4F46E5' : '#1A1A1E', textTransform: 'capitalize' }}>{t}</button>
        ))}
        <button onClick={() => setAutoRefresh(!autoRefresh)} style={{ ...btn, background: autoRefresh ? '#22C55E' : '#1A1A1E' }}>{autoRefresh ? '⏸ Auto' : '▶ Auto'}</button>
      </div>

      {tab === 'explore' && dashboard && (
        <div style={{ display: 'grid', gap: '12px' }}>
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            {[
              { l: 'Total NFTs', v: dashboard.stats?.total_nfts || 0 },
              { l: 'Collections', v: dashboard.stats?.total_collections || 0 },
              { l: 'Active Listings', v: dashboard.stats?.active_listings || 0 },
              { l: 'Active Auctions', v: dashboard.stats?.active_auctions || 0 },
              { l: 'Total Volume', v: fmt(dashboard.stats?.total_volume || 0) },
              { l: 'Sold', v: dashboard.stats?.sold_listings || 0 },
              { l: 'Transfers', v: dashboard.stats?.total_transfers || 0 },
              { l: 'Avg Sale', v: fmt(dashboard.stats?.avg_sale_price || 0) },
            ].map(s => (
              <div key={s.l} style={{ ...panel, flex: '1 1 100px', textAlign: 'center' }}>
                <div style={{ fontSize: '10px', color: '#888' }}>{s.l}</div>
                <div style={{ fontSize: '16px', fontWeight: 700 }}>{s.v}</div>
              </div>
            ))}
          </div>

          {/* Top Collections */}
          <div style={panel}>
            <div style={{ fontSize: '14px', fontWeight: 600, marginBottom: '8px' }}>Top Collections</div>
            {dashboard.top_collections?.map((c, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', borderBottom: '1px solid #222', fontSize: '12px' }}>
                <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                  <span style={{ color: '#888' }}>#{i+1}</span>
                  <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: typeColor[c.collection_type] || '#888' }} />
                  <span>{c.name}</span>
                  {c.verified && <span style={{ color: '#4F46E5', fontSize: '10px' }}>✓</span>}
                </div>
                <div style={{ display: 'flex', gap: '12px', fontSize: '10px', color: '#888' }}>
                  <span>Floor: {fmt(c.floor_price || 0)}</span>
                  <span>Supply: {c.total_supply}/{c.max_supply}</span>
                  <span style={{ color: '#4F46E5' }}>Vol: {fmt(c.total_volume || 0)}</span>
                </div>
              </div>
            ))}
          </div>

          {/* Recent Sales */}
          <div style={panel}>
            <div style={{ fontSize: '14px', fontWeight: 600, marginBottom: '8px' }}>Recent Sales</div>
            {dashboard.recent_sales?.slice(0, 10).map((l, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', borderBottom: '1px solid #222', fontSize: '12px' }}>
                <span>{l.collection_name}</span>
                <div style={{ display: 'flex', gap: '8px', fontSize: '10px' }}>
                  <span style={{ color: '#4F46E5' }}>{fmt(l.sold_price || 0)} VRS</span>
                  <span style={{ color: '#888' }}>{l.buyer?.slice(0, 8)}...</span>
                </div>
              </div>
            ))}
            {(!dashboard.recent_sales || dashboard.recent_sales.length === 0) && <div style={{ fontSize: '12px', color: '#888', textAlign: 'center', padding: '20px' }}>No sales yet</div>}
          </div>
        </div>
      )}

      {tab === 'collections' && (
        <div style={{ display: 'grid', gap: '6px' }}>
          {collections.map((c, i) => (
            <div key={i} style={panel}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                  <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: typeColor[c.collection_type] || '#888' }} />
                  <div>
                    <div style={{ fontSize: '13px', fontWeight: 600 }}>{c.name} {c.verified && <span style={{ color: '#4F46E5', fontSize: '10px' }}>✓ verified</span>}</div>
                    <div style={{ fontSize: '11px', color: '#888' }}>{c.description}</div>
                  </div>
                </div>
                <span style={{ fontSize: '9px', padding: '2px 6px', borderRadius: '4px', background: (typeColor[c.collection_type] || '#888') + '22', color: typeColor[c.collection_type] || '#888', textTransform: 'capitalize' }}>{c.collection_type.replace('_', ' ')}</span>
              </div>
              <div style={{ display: 'flex', gap: '12px', fontSize: '11px', marginTop: '8px', color: '#888', flexWrap: 'wrap' }}>
                <span>Supply: <b>{c.total_supply}/{c.max_supply}</b></span>
                <span>Floor: <b style={{ color: '#4F46E5' }}>{fmt(c.floor_price || 0)} VRS</b></span>
                <span>Mint: {fmt(c.mint_price)} VRS</span>
                <span>Royalty: {c.royalty_bps / 100}%</span>
                <span>Volume: {fmt(c.total_volume || 0)} VRS</span>
                <span>Standard: {c.standard}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {tab === 'listings' && (
        <div style={{ display: 'grid', gap: '6px' }}>
          {listings.map((l, i) => (
            <div key={i} style={panel}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <div style={{ fontSize: '13px', fontWeight: 600'>{l.collection_name}</div>
                <div style={{ display: 'flex', gap: '4px' }}>
                  <span style={{ fontSize: '9px', padding: '2px 6px', borderRadius: '4px', background: '#4F46E522', color: '#4F46E5' }}>{l.listing_type === 'auction' ? '🔨 Auction' : '🏷️ Fixed'}</span>
                  <span style={{ fontSize: '9px', padding: '2px 6px', borderRadius: '4px', background: (statusColor[l.status] || '#888') + '22', color: statusColor[l.status] || '#888' }}>{l.status}</span>
                </div>
              </div>
              <div style={{ display: 'flex', gap: '12px', fontSize: '11px', marginTop: '4px', color: '#888', flexWrap: 'wrap' }}>
                <span>Token #{l.token_id}</span>
                <span>Price: <b style={{ color: '#4F46E5' }}>{fmt(l.price)} {l.currency}</b></span>
                <span>Seller: {l.seller?.slice(0, 10)}...</span>
                <span>Views: {l.views}</span>
                <span>Favorites: {l.favorites}</span>
              </div>
              {l.listing_type === 'fixed_price' && l.status === 'active' && (
                <button onClick={() => handleBuy(l.id)} style={{ ...btn, background: '#4F46E5', fontSize: '11px', padding: '4px 12px', marginTop: '8px' }}>Buy Now</button>
              )}
            </div>
          ))}
          {listings.length === 0 && <div style={{ fontSize: '12px', color: '#888', textAlign: 'center', padding: '20px' }}>No active listings</div>}
        </div>
      )}
    </div>
  );
}

export default NftMarketplace;
