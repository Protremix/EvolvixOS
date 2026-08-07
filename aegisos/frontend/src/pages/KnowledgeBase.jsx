import React, { useState, useEffect, useCallback } from 'react';
import kbService from '../services/knowledgeBaseService';

function KnowledgeBase() {
  const [entries, setEntries] = useState([]);
  const [stats, setStats] = useState(null);
  const [patterns, setPatterns] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState(null);
  const [category, setCategory] = useState(null);
  const [showCreate, setShowCreate] = useState(false);
  const [loading, setLoading] = useState(true);

  const fetchAll = useCallback(async () => {
    try {
      const [entriesResp, statsResp, patternsResp] = await Promise.all([
        kbService.list(category ? { category } : {}),
        kbService.stats(),
        kbService.patterns(),
      ]);
      setEntries(entriesResp.data);
      setStats(statsResp.data);
      setPatterns(patternsResp.data);
    } catch (err) { console.error('Failed to load', err); }
    finally { setLoading(false); }
  }, [category]);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  const handleSearch = async () => {
    if (!searchQuery.trim()) { setSearchResults(null); return; }
    try {
      const resp = await kbService.search(searchQuery);
      setSearchResults(resp.data);
    } catch (err) { console.error('Search failed', err); }
  };

  const handleExtractPatterns = async () => {
    try {
      const resp = await kbService.extractPatterns();
      setPatterns(resp.data);
    } catch (err) { console.error('Extract failed', err); }
  };

  if (loading) return <div style={{ padding: '24px', color: '#888' }}>Loading knowledge base...</div>;

  const catColors = {
    architecture: '#4F46E5', security: '#EF4444', testing: '#22C55E',
    performance: '#FFA500', devops: '#06B6D4', general: '#888',
  };

  return (
    <div style={{ padding: '24px' }}>
      <h1 style={{ fontSize: '28px', fontWeight: 700, margin: '0 0 8px' }}>Knowledge Base</h1>
      <p style={{ color: '#888', marginBottom: '24px' }}>Lessons learned, best practices, and detected patterns</p>

      {/* Stats */}
      {stats && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))', gap: '12px', marginBottom: '24px' }}>
          <StatCard label="Total Entries" value={stats.total_entries} />
          <StatCard label="Patterns Detected" value={stats.total_patterns} />
          <StatCard label="Total References" value={stats.total_references} />
          <StatCard label="Avg Confidence" value={stats.avg_confidence} />
        </div>
      )}

      {/* Search */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '24px' }}>
        <input
          placeholder="Search knowledge base..."
          value={searchQuery}
          onChange={e => setSearchQuery(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleSearch()}
          style={{ ...inputStyle, flex: 1 }}
        />
        <button onClick={handleSearch} style={btnPrimary}>Search</button>
        <button onClick={() => setShowCreate(!showCreate)} style={{ ...btnPrimary, background: '#374151' }}>
          {showCreate ? 'Cancel' : '+ Add Entry'}
        </button>
        <button onClick={handleExtractPatterns} style={{ ...btnPrimary, background: '#0D3D1A', color: '#22C55E' }}>
          Extract Patterns
        </button>
      </div>

      {showCreate && <CreateEntryForm onCreate={async (e) => { await kbService.create(e); setShowCreate(false); fetchAll(); }} />}

      {/* Category Filter */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '24px', flexWrap: 'wrap' }}>
        <button onClick={() => setCategory(null)} style={category === null ? catActive : catBtn}>All</button>
        {stats && Object.entries(stats.categories || {}).map(([cat, count]) => (
          <button key={cat} onClick={() => setCategory(cat)} style={category === cat ? catActive : catBtn}>
            <span style={{ color: catColors[cat] || '#888' }}>●</span> {cat} ({count})
          </button>
        ))}
      </div>

      {/* Search Results or Entry List */}
      {searchResults ? (
        <div>
          <h2 style={{ fontSize: '18px', marginBottom: '12px' }}>Search Results ({searchResults.length})</h2>
          {searchResults.map((r, i) => (
            <EntryCard key={i} entry={r.entry} score={r.score} catColors={catColors} />
          ))}
        </div>
      ) : (
        <div>
          <h2 style={{ fontSize: '18px', marginBottom: '12px' }}>Knowledge Entries ({entries.length})</h2>
          {entries.map(e => (
            <EntryCard key={e.id} entry={e} catColors={catColors} onDelete={async () => { await kbService.delete(e.id); fetchAll(); }} />
          ))}
        </div>
      )}

      {/* Patterns */}
      {patterns.length > 0 && (
        <div style={{ marginTop: '24px' }}>
          <h2 style={{ fontSize: '18px', marginBottom: '12px' }}>Detected Patterns ({patterns.length})</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {patterns.map(p => (
              <div key={p.id} style={{ background: '#1A1A1E', borderRadius: '8px', padding: '12px', border: '1px solid #333', borderLeft: `3px solid ${patternColor(p.pattern_type)}` }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ fontWeight: 600, color: patternColor(p.pattern_type) }}>{patternIcon(p.pattern_type)} {p.pattern_type.replace(/_/g, ' ')}</span>
                  <span style={{ fontSize: '12px', color: '#666' }}>Stage: {p.stage} · Agent: {p.agent} · Occurrences: {p.occurrence_count}</span>
                </div>
                <div style={{ fontSize: '13px', color: '#CCC', marginTop: '4px' }}>{p.description}</div>
                <div style={{ fontSize: '12px', color: '#FFA500', marginTop: '4px' }}>→ {p.recommendation}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function EntryCard({ entry, score, catColors, onDelete }) {
  const [expanded, setExpanded] = useState(false);
  const color = catColors[entry.category] || '#888';
  return (
    <div style={{ background: '#1A1A1E', borderRadius: '8px', padding: '16px', marginBottom: '8px', border: '1px solid #333', borderLeft: `3px solid ${color}` }}>
      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '10px', padding: '2px 6px', borderRadius: '4px', background: color + '22', color }}>{entry.category}</span>
          <span style={{ fontWeight: 600 }}>{entry.title}</span>
          {score && <span style={{ fontSize: '11px', color: '#4F46E5' }}>score: {score}</span>}
        </div>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <span style={{ fontSize: '11px', color: '#666' }}>confidence: {entry.confidence}</span>
          {onDelete && <button onClick={onDelete} style={{ ...btnSmall, background: '#5C1A1A' }}>Delete</button>}
        </div>
      </div>
      <div style={{ fontSize: '13px', color: '#999', marginTop: '4px' }}>
        {expanded ? entry.content : entry.content.slice(0, 150) + (entry.content.length > 150 ? '...' : '')}
        {entry.content.length > 150 && <button onClick={() => setExpanded(!expanded)} style={{ background: 'none', border: 'none', color: '#4F46E5', cursor: 'pointer', fontSize: '12px' }}>{expanded ? ' less' : ' more'}</button>}
      </div>
      {entry.tags && entry.tags.length > 0 && (
        <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap', marginTop: '4px' }}>
          {entry.tags.map((t, i) => <span key={i} style={{ fontSize: '10px', padding: '2px 6px', background: '#2A2A2E', borderRadius: '4px', color: '#888' }}>{t}</span>)}
        </div>
      )}
    </div>
  );
}

function CreateEntryForm({ onCreate }) {
  const [form, setForm] = useState({ title: '', content: '', category: 'general', tags: [], confidence: 0.5 });
  const [tagInput, setTagInput] = useState('');
  return (
    <form onSubmit={e => { e.preventDefault(); onCreate({ ...form, tags: form.tags }); }} style={{ background: '#1A1A1E', padding: '20px', borderRadius: '10px', marginBottom: '24px' }}>
      <h2 style={{ fontSize: '18px', marginBottom: '12px' }}>Add Knowledge Entry</h2>
      <input placeholder="Title" value={form.title} onChange={e => setForm({...form, title: e.target.value})} style={{ ...inputStyle, width: '100%', marginBottom: '8px' }} required />
      <textarea placeholder="Content" value={form.content} onChange={e => setForm({...form, content: e.target.value})} style={{ ...inputStyle, width: '100%', minHeight: '80px', marginBottom: '8px', resize: 'vertical' }} required />
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
        <select value={form.category} onChange={e => setForm({...form, category: e.target.value})} style={inputStyle}>
          <option value="general">General</option><option value="architecture">Architecture</option>
          <option value="security">Security</option><option value="testing">Testing</option>
          <option value="performance">Performance</option><option value="devops">DevOps</option>
        </select>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <input type="number" min="0" max="1" step="0.1" value={form.confidence} onChange={e => setForm({...form, confidence: parseFloat(e.target.value)})} style={inputStyle} />
          <span style={{ fontSize: '12px', color: '#888' }}>Confidence</span>
        </div>
      </div>
      <div style={{ display: 'flex', gap: '8px', marginTop: '8px' }}>
        <input placeholder="Add tag..." value={tagInput} onChange={e => setTagInput(e.target.value)} onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); if (tagInput.trim()) { setForm({...form, tags: [...form.tags, tagInput.trim()]}); setTagInput(''); }}}} style={inputStyle} />
        {form.tags.map((t, i) => <span key={i} style={{ fontSize: '12px', padding: '2px 8px', background: '#2A2A2E', borderRadius: '4px' }}>{t}</span>)}
      </div>
      <button type="submit" style={{ marginTop: '12px', ...btnPrimary }}>Create Entry</button>
    </form>
  );
}

function StatCard({ label, value }) {
  return (
    <div style={{ background: '#1A1A1E', borderRadius: '10px', padding: '16px', border: '1px solid #333' }}>
      <div style={{ fontSize: '13px', color: '#888' }}>{label}</div>
      <div style={{ fontSize: '24px', fontWeight: 700, marginTop: '4px' }}>{value}</div>
    </div>
  );
}

function patternColor(type) {
  return { failure_pattern: '#EF4444', success_pattern: '#22C55E', retry_pattern: '#FFA500', bottleneck_pattern: '#FF6B6B' }[type] || '#888';
}
function patternIcon(type) {
  return { failure_pattern: '✗', success_pattern: '✓', retry_pattern: '↻', bottleneck_pattern: '⚠' }[type] || '•';
}

const inputStyle = { padding: '8px 12px', background: '#0D0D0F', border: '1px solid #333', borderRadius: '6px', color: '#fff', fontSize: '14px' };
const btnPrimary = { padding: '8px 16px', background: '#4F46E5', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer' };
const btnSmall = { padding: '4px 12px', background: '#4F46E5', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '12px' };
const catBtn = { padding: '6px 14px', background: '#1A1A1E', border: '1px solid #333', borderRadius: '6px', color: '#888', cursor: 'pointer', fontSize: '13px' };
const catActive = { ...catBtn, background: '#4F46E5', color: '#fff', border: '1px solid #4F46E5' };

export default KnowledgeBase;
