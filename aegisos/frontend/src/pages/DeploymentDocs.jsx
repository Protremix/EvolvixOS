import React, { useState, useEffect, useCallback } from 'react';
import docsService from '../services/docsService';

function DeploymentDocs() {
  const [tab, setTab] = useState('docs');
  const [dashboard, setDashboard] = useState(null);
  const [docs, setDocs] = useState([]);
  const [manifests, setManifests] = useState([]);
  const [faqs, setFaqs] = useState([]);
  const [runbooks, setRunbooks] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');

  const fetchData = useCallback(async () => {
    try {
      const [dash, d, m, f, r] = await Promise.all([
        docsService.dashboard(),
        docsService.list({ limit: 50 }),
        docsService.manifests(),
        docsService.faqs(),
        docsService.runbooks(),
      ]);
      setDashboard(dash.data || null);
      setDocs(d.data || []);
      setManifests(m.data || []);
      setFaqs(f.data || []);
      setRunbooks(r.data || []);
    } catch (err) { console.error(err); }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleSearch = async () => {
    try { const r = await docsService.search(searchQuery); setDocs(r.data || []); } catch (e) { console.error(e); }
  };

  const panel = { background: '#1A1A1E', borderRadius: '10px', border: '1px solid #333', padding: '14px' };
  const btn = { padding: '8px 16px', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '13px', color: '#fff' };
  const input = { padding: '8px 12px', background: '#0D0D0F', border: '1px solid #333', borderRadius: '6px', color: '#fff', fontSize: '13px', width: '100%' };
  const sevColor = { critical: '#EF4444', high: '#F97316', medium: '#FFA500', low: '#4F46E5' };
  const manTypeColor = { 'docker-compose': '#4F46E5', kubernetes: '#3B82F6', systemd: '#22C55E', nginx: '#A855F7', 'env-template': '#FFA500', dockerfile: '#06B6D4' };

  return (
    <div style={{ padding: '24px' }}>
      <h1 style={{ fontSize: '28px', fontWeight: 700, marginBottom: '4px' }}>📚 Documentation & Deployment</h1>
      <p style={{ color: '#888', marginBottom: '12px' }}>Complete docs, manifests, FAQs, and runbooks</p>

      {dashboard && (
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '12px' }}>
          {[
            { l: 'Docs', v: dashboard.stats?.total_docs || 0 },
            { l: 'Manifests', v: dashboard.stats?.total_manifests || 0 },
            { l: 'FAQs', v: dashboard.stats?.total_faqs || 0 },
            { l: 'Runbooks', v: dashboard.stats?.total_runbooks || 0 },
            { l: 'Words', v: dashboard.stats?.total_words || 0 },
            { l: 'Categories', v: dashboard.stats?.doc_categories || 0 },
          ].map(s => (
            <div key={s.l} style={{ ...panel, flex: '1 1 100px', textAlign: 'center' }}>
              <div style={{ fontSize: '10px', color: '#888' }}>{s.l}</div>
              <div style={{ fontSize: '16px', fontWeight: 700 }}>{s.v}</div>
            </div>
          ))}
        </div>
      )}

      <div style={{ display: 'flex', gap: '4px', marginBottom: '12px', flexWrap: 'wrap' }}>
        {['docs', 'manifests', 'faqs', 'runbooks'].map(t => (
          <button key={t} onClick={() => setTab(t)} style={{ ...btn, background: tab === t ? '#4F46E5' : '#1A1A1E', textTransform: 'capitalize' }}>{t}</button>
        ))}
      </div>

      {tab === 'docs' && (
        <div style={{ display: 'grid', gap: '12px' }}>
          <div style={{ display: 'flex', gap: '8px' }}>
            <input value={searchQuery} onChange={e => setSearchQuery(e.target.value)} placeholder="Search docs..." style={input} onKeyDown={e => e.key === 'Enter' && handleSearch()} />
            <button onClick={handleSearch} style={{ ...btn, background: '#4F46E5' }}>Search</button>
          </div>
          {docs.map((d, i) => (
            <div key={i} style={panel}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <div style={{ fontSize: '13px', fontWeight: 600 }}>{d.title}</div>
                <span style={{ fontSize: '9px', padding: '2px 6px', borderRadius: '4px', background: '#4F46E522', color: '#4F46E5' }}>{d.category}</span>
              </div>
              <div style={{ fontSize: '11px', color: '#888', marginTop: '4px' }}>{d.description}</div>
              <div style={{ fontSize: '10px', color: '#666', marginTop: '4px' }}>📄 {d.word_count} words | Sections: {d.sections?.join(', ')}</div>
              {d.tags?.length > 0 && <div style={{ fontSize: '10px', color: '#4F46E5', marginTop: '4px' }}>#{d.tags.join(' #')}</div>}
            </div>
          ))}
        </div>
      )}

      {tab === 'manifests' && (
        <div style={{ display: 'grid', gap: '6px' }}>
          {manifests.map((m, i) => (
            <div key={i} style={panel}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <div style={{ fontSize: '13px', fontWeight: 600 }}>{m.name}</div>
                <span style={{ fontSize: '9px', padding: '2px 6px', borderRadius: '4px', background: (manTypeColor[m.type] || '#888') + '22', color: manTypeColor[m.type] || '#888' }}>{m.type}</span>
              </div>
              <div style={{ fontSize: '11px', color: '#888', marginTop: '4px' }}>{m.description}</div>
              <div style={{ fontSize: '10px', color: '#666', marginTop: '4px' }}>📁 {m.filename} | Component: {m.component} | Port: {m.port || 'N/A'}</div>
              {m.env_vars?.length > 0 && <div style={{ fontSize: '10px', color: '#FFA500', marginTop: '2px' }}>Env: {m.env_vars.join(', ')}</div>}
              {m.dependencies?.length > 0 && <div style={{ fontSize: '10px', color: '#22C55E', marginTop: '2px' }}>Deps: {m.dependencies.join(', ')}</div>}
            </div>
          ))}
        </div>
      )}

      {tab === 'faqs' && (
        <div style={{ display: 'grid', gap: '6px' }}>
          {faqs.map((f, i) => (
            <div key={i} style={panel}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <div style={{ fontSize: '13px', fontWeight: 600 }}>{f.question}</div>
                <span style={{ fontSize: '9px', padding: '2px 6px', borderRadius: '4px', background: '#222', color: '#888' }}>{f.category}</span>
              </div>
              <div style={{ fontSize: '11px', color: '#888', marginTop: '4px' }}>{f.answer}</div>
              <div style={{ fontSize: '10px', color: '#666', marginTop: '4px' }}>👍 {f.helpful_count} found this helpful</div>
            </div>
          ))}
        </div>
      )}

      {tab === 'runbooks' && (
        <div style={{ display: 'grid', gap: '6px' }}>
          {runbooks.map((r, i) => (
            <div key={i} style={{ ...panel, borderLeft: `3px solid ${sevColor[r.severity] || '#888'}` }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <div style={{ fontSize: '13px', fontWeight: 600 }}>{r.name}</div>
                <div style={{ display: 'flex', gap: '4px' }}>
                  <span style={{ fontSize: '9px', padding: '2px 6px', borderRadius: '4px', background: (sevColor[r.severity] || '#888') + '22', color: sevColor[r.severity] || '#888' }}>{r.severity}</span>
                  <span style={{ fontSize: '9px', padding: '2px 6px', borderRadius: '4px', background: '#222', color: '#888' }}>⏱ {r.estimated_time}</span>
                </div>
              </div>
              <div style={{ fontSize: '11px', color: '#888', marginTop: '4px' }}>{r.scenario}</div>
              <div style={{ fontSize: '11px', color: '#4F46E5', marginTop: '4px' }}>Steps:</div>
              {r.steps?.map((s, j) => <div key={j} style={{ fontSize: '11px', color: '#aaa', paddingLeft: '8px' }}>{j + 1}. {s}</div>)}
              {r.rollback_steps?.length > 0 && <div style={{ fontSize: '11px', color: '#EF4444', marginTop: '4px' }}>Rollback:</div>}
              {r.rollback_steps?.map((s, j) => <div key={j} style={{ fontSize: '11px', color: '#aaa', paddingLeft: '8px' }}>↩ {s}</div>)}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default DeploymentDocs;
