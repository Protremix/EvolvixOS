import React, { useState, useEffect, useCallback } from 'react';
import pluginService from '../services/pluginService';

function PluginMarketplace() {
  const [tab, setTab] = useState('browse');
  const [dashboard, setDashboard] = useState(null);
  const [plugins, setPlugins] = useState([]);
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('');
  const [sortBy, setSortBy] = useState('downloads');
  const [submitForm, setSubmitForm] = useState({ name: '', description: '', author: '', version: '1.0.0', category: 'utility', license: 'free', tags: '', homepage: '', repository: '' });

  const fetchData = useCallback(async () => {
    try {
      const [dash, plgs] = await Promise.all([
        pluginService.dashboard(),
        pluginService.list({ status: 'approved', sort_by: sortBy, search, category, limit: 50 }),
      ]);
      setDashboard(dash.data || null);
      setPlugins(plgs.data || []);
    } catch (err) { console.error(err); }
  }, [search, category, sortBy]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleSubmit = async () => {
    try {
      const tags = submitForm.tags ? submitForm.tags.split(',').map(t => t.trim()) : [];
      await pluginService.submit({ ...submitForm, tags });
      setSubmitForm({ name: '', description: '', author: '', version: '1.0.0', category: 'utility', license: 'free', tags: '', homepage: '', repository: '' });
      fetchData();
    } catch (e) { console.error(e); }
  };

  const handleInstall = async (id) => {
    try { await pluginService.install(id, '0xcurrent_user'); fetchData(); } catch (e) { console.error(e); }
  };

  const fmt = (n) => n >= 1e6 ? `${(n/1e6).toFixed(1)}M` : n >= 1e3 ? `${(n/1e3).toFixed(1)}K` : n;
  const licenseColor = { free: '#22C55E', freemium: '#FFA500', paid: '#4F46E5', open_source: '#8B5CF6' };
  const panel = { background: '#1A1A1E', borderRadius: '10px', border: '1px solid #333', padding: '14px' };
  const btn = { padding: '8px 16px', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '13px', color: '#fff' };
  const input = { padding: '8px 12px', background: '#0D0D0F', border: '1px solid #333', borderRadius: '6px', color: '#fff', fontSize: '13px', width: '100%' };

  return (
    <div style={{ padding: '24px' }}>
      <h1 style={{ fontSize: '28px', fontWeight: 700, marginBottom: '4px' }}>🧩 Plugin Marketplace</h1>
      <p style={{ color: '#888', marginBottom: '12px' }}>Extend the EvolvixOS ecosystem</p>

      <div style={{ display: 'flex', gap: '4px', marginBottom: '12px' }}>
        {['browse', 'submit', 'manage'].map(t => (
          <button key={t} onClick={() => setTab(t)} style={{ ...btn, background: tab === t ? '#4F46E5' : '#1A1A1E', textTransform: 'capitalize' }}>{t}</button>
        ))}
      </div>

      {tab === 'browse' && (
        <div style={{ display: 'grid', gap: '12px' }}>
          {/* Search & filters */}
          <div style={{ display: 'flex', gap: '8px' }}>
            <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search plugins..." style={input} />
            <select value={category} onChange={e => setCategory(e.target.value)} style={{ ...input, maxWidth: '150px' }}>
              <option value="">All categories</option>
              {dashboard?.categories?.map(c => <option key={c.value} value={c.value}>{c.name} ({c.count})</option>)}
            </select>
            <select value={sortBy} onChange={e => setSortBy(e.target.value)} style={{ ...input, maxWidth: '120px' }}>
              <option value="downloads">Downloads</option>
              <option value="rating">Rating</option>
              <option value="newest">Newest</option>
              <option value="name">Name</option>
            </select>
          </div>

          {/* Stats */}
          {dashboard && (
            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
              {[{ l: 'Plugins', v: dashboard.stats?.total_plugins }, { l: 'Approved', v: dashboard.stats?.approved }, { l: 'Downloads', v: fmt(dashboard.stats?.total_downloads || 0) }, { l: 'Developers', v: dashboard.stats?.total_developers }, { l: 'Avg Rating', v: dashboard.stats?.avg_rating }, { l: 'Reviews', v: dashboard.stats?.total_reviews }].map(s => (
                <div key={s.l} style={{ ...panel, flex: '1 1 100px', textAlign: 'center' }}>
                  <div style={{ fontSize: '10px', color: '#888' }}>{s.l}</div>
                  <div style={{ fontSize: '16px', fontWeight: 700 }}>{s.v}</div>
                </div>
              ))}
            </div>
          )}

          {/* Plugin grid */}
          {plugins.map((p, i) => (
            <div key={i} style={panel}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                <div>
                  <div style={{ fontSize: '13px', fontWeight: 600 }}>{p.name}</div>
                  <div style={{ fontSize: '11px', color: '#888' }}>{p.description}</div>
                </div>
                <span style={{ fontSize: '9px', padding: '2px 6px', borderRadius: '4px', background: (licenseColor[p.license] || '#888') + '22', color: licenseColor[p.license] || '#888', textTransform: 'capitalize' }}>{p.license}</span>
              </div>
              <div style={{ display: 'flex', gap: '12px', fontSize: '11px', marginTop: '8px', color: '#888', flexWrap: 'wrap' }}>
                <span>⬇ {fmt(p.downloads)}</span>
                <span>⭐ {p.rating}</span>
                <span>v{p.version}</span>
                <span style={{ textTransform: 'capitalize' }}>{p.category.replace('_', ' ')}</span>
                <span>{p.author}</span>
              </div>
              {p.tags?.length > 0 && (
                <div style={{ display: 'flex', gap: '4px', marginTop: '6px' }}>
                  {p.tags.map((t, j) => <span key={j} style={{ fontSize: '9px', padding: '2px 6px', borderRadius: '3px', background: '#333', color: '#888' }}>{t}</span>)}
                </div>
              )}
              <button onClick={() => handleInstall(p.id)} style={{ ...btn, background: '#4F46E5', marginTop: '8px', fontSize: '11px', padding: '4px 12px' }}>Install</button>
            </div>
          ))}
        </div>
      )}

      {tab === 'submit' && (
        <div style={{ ...panel, maxWidth: '600px' }}>
          <div style={{ fontSize: '14px', fontWeight: 600, marginBottom: '12px' }}>Submit Plugin</div>
          <div style={{ display: 'grid', gap: '8px' }}>
            <input value={submitForm.name} onChange={e => setSubmitForm({ ...submitForm, name: e.target.value })} placeholder="Plugin name" style={input} />
            <textarea value={submitForm.description} onChange={e => setSubmitForm({ ...submitForm, description: e.target.value })} placeholder="Description" style={{ ...input, minHeight: '60px' }} />
            <input value={submitForm.author} onChange={e => setSubmitForm({ ...submitForm, author: e.target.value })} placeholder="Author address" style={input} />
            <div style={{ display: 'flex', gap: '8px' }}>
              <input value={submitForm.version} onChange={e => setSubmitForm({ ...submitForm, version: e.target.value })} placeholder="Version" style={input} />
              <select value={submitForm.category} onChange={e => setSubmitForm({ ...submitForm, category: e.target.value })} style={input}>
                {['analytics', 'security', 'developer_tools', 'wallet', 'governance', 'defi', 'nft', 'bridge', 'identity', 'monitoring', 'ai', 'utility'].map(c => <option key={c} value={c}>{c.replace('_', ' ')}</option>)}
              </select>
              <select value={submitForm.license} onChange={e => setSubmitForm({ ...submitForm, license: e.target.value })} style={input}>
                <option value="free">Free</option><option value="freemium">Freemium</option><option value="paid">Paid</option><option value="open_source">Open Source</option>
              </select>
            </div>
            <input value={submitForm.tags} onChange={e => setSubmitForm({ ...submitForm, tags: e.target.value })} placeholder="Tags (comma separated)" style={input} />
            <input value={submitForm.homepage} onChange={e => setSubmitForm({ ...submitForm, homepage: e.target.value })} placeholder="Homepage URL" style={input} />
            <input value={submitForm.repository} onChange={e => setSubmitForm({ ...submitForm, repository: e.target.value })} placeholder="Repository URL" style={input} />
            <button onClick={handleSubmit} style={{ ...btn, background: '#4F46E5' }}>Submit for Review</button>
          </div>
        </div>
      )}

      {tab === 'manage' && dashboard && (
        <div style={{ display: 'grid', gap: '12px' }}>
          <div style={panel}>
            <div style={{ fontSize: '13px', fontWeight: 600, marginBottom: '8px' }}>Featured Plugins</div>
            {dashboard.featured?.map((p, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', borderBottom: '1px solid #222' }}>
                <div style={{ fontSize: '12px' }}>{p.name}</div>
                <div style={{ fontSize: '12px', color: '#4F46E5' }}>⭐ {p.rating}</div>
              </div>
            ))}
          </div>
          <div style={panel}>
            <div style={{ fontSize: '13px', fontWeight: 600, marginBottom: '8px' }}>Popular Plugins</div>
            {dashboard.popular?.map((p, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', borderBottom: '1px solid #222' }}>
                <div style={{ fontSize: '12px' }}>{p.name}</div>
                <div style={{ fontSize: '12px', color: '#888' }}>⬇ {fmt(p.downloads)}</div>
              </div>
            ))}
          </div>
          <div style={panel}>
            <div style={{ fontSize: '13px', fontWeight: 600, marginBottom: '8px' }}>Newest Plugins</div>
            {dashboard.newest?.map((p, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', borderBottom: '1px solid #222' }}>
                <div style={{ fontSize: '12px' }}>{p.name}</div>
                <div style={{ fontSize: '12px', color: '#888' }}>{new Date(p.created).toLocaleDateString()}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default PluginMarketplace;
