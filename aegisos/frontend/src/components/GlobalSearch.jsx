import React, { useState, useEffect, useRef } from 'react';
import searchService from '../services/searchService';

function GlobalSearch() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [showResults, setShowResults] = useState(false);
  const [loading, setLoading] = useState(false);
  const [searchTypes, setSearchTypes] = useState([]);
  const ref = useRef(null);

  useEffect(() => {
    searchService.types().then(r => setSearchTypes(r.data)).catch(() => {});
    
    const handleClick = (e) => {
      if (ref.current && !ref.current.contains(e.target)) {
        setShowResults(false);
      }
    };
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  useEffect(() => {
    if (query.length < 2) { setResults([]); return; }
    const timer = setTimeout(async () => {
      setLoading(true);
      try {
        const resp = await searchService.search(query, null, 20);
        setResults(resp.data);
        setShowResults(true);
      } catch (err) { console.error(err); }
      finally { setLoading(false); }
    }, 300);
    return () => clearTimeout(timer);
  }, [query]);

  const entityColors = {
    pipeline: '#4F46E5', knowledge: '#06B6D4', activity: '#FFA500',
    webhook: '#22C55E', setting: '#888', template: '#EC4899',
  };

  return (
    <div ref={ref} style={{ position: 'relative', width: '100%' }}>
      <input
        type="text"
        placeholder="Search everything..."
        value={query}
        onChange={e => setQuery(e.target.value)}
        onFocus={() => results.length > 0 && setShowResults(true)}
        style={searchBarStyle}
      />
      {showResults && query.length >= 2 && (
        <div style={resultsContainerStyle}>
          {loading && <div style={{ padding: '8px', color: '#666', fontSize: '13px' }}>Searching...</div>}
          {!loading && results.length === 0 && (
            <div style={{ padding: '8px', color: '#666', fontSize: '13px' }}>No results found</div>
          )}
          {results.map((r, i) => (
            <div key={i} style={resultItemStyle} onClick={() => { setShowResults(false); setQuery(''); }}>
              <span style={{ ...entityBadge, background: (entityColors[r.entity_type] || '#888') + '22', color: entityColors[r.entity_type] || '#888' }}>
                {r.entity_type}
              </span>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: '13px', fontWeight: 600, color: '#CCC' }}>{r.title}</div>
                <div style={{ fontSize: '11px', color: '#666' }}>{r.description}</div>
              </div>
              <span style={{ fontSize: '10px', color: '#444' }}>{r.relevance}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

const searchBarStyle = {
  width: '100%', padding: '8px 12px', background: '#0D0D0F',
  border: '1px solid #333', borderRadius: '8px', color: '#fff',
  fontSize: '14px', outline: 'none',
};
const resultsContainerStyle = {
  position: 'absolute', top: '100%', left: 0, right: 0,
  background: '#1A1A1E', border: '1px solid #333', borderRadius: '8px',
  marginTop: '4px', maxHeight: '400px', overflowY: 'auto', zIndex: 100,
  boxShadow: '0 4px 12px rgba(0,0,0,0.5)',
};
const resultItemStyle = {
  display: 'flex', alignItems: 'center', gap: '8px',
  padding: '8px 12px', cursor: 'pointer', borderBottom: '1px solid #222',
};
const entityBadge = {
  fontSize: '9px', padding: '2px 6px', borderRadius: '4px',
  textTransform: 'uppercase', fontWeight: 600, minWidth: '60px', textAlign: 'center',
};

export default GlobalSearch;
