import React, { useState, useEffect, useCallback } from 'react';
import activityLogService from '../services/activityLogService';

function ActivityLog() {
  const [entries, setEntries] = useState([]);
  const [stats, setStats] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterAction, setFilterAction] = useState('');
  const [filterSeverity, setFilterSeverity] = useState('');
  const [loading, setLoading] = useState(true);

  const fetchAll = useCallback(async () => {
    try {
      const params = { limit: 100 };
      if (filterAction) params.action = filterAction;
      if (filterSeverity) params.severity = filterSeverity;
      const [entriesResp, statsResp] = await Promise.all([
        activityLogService.list(params),
        activityLogService.stats(),
      ]);
      setEntries(entriesResp.data);
      setStats(statsResp.data);
    } catch (err) { console.error('Failed', err); }
    finally { setLoading(false); }
  }, [filterAction, filterSeverity]);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  const handleSearch = async () => {
    if (!searchQuery.trim()) { fetchAll(); return; }
    try {
      const resp = await activityLogService.search(searchQuery);
      setEntries(resp.data);
    } catch (err) { console.error(err); }
  };

  if (loading) return <div style={{ padding: '24px', color: '#888' }}>Loading activity log...</div>;

  const sevColors = { info: '#4F46E5', warning: '#FFA500', error: '#EF4444' };

  return (
    <div style={{ padding: '24px' }}>
      <h1 style={{ fontSize: '28px', fontWeight: 700, margin: '0 0 8px' }}>Activity Log</h1>
      <p style={{ color: '#888', marginBottom: '24px' }}>Audit trail of all user and system actions</p>

      {/* Stats */}
      {stats && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))', gap: '12px', marginBottom: '24px' }}>
          <StatCard label="Total Entries" value={stats.total_entries} />
          <StatCard label="Errors" value={stats.severities?.error || 0} color="#EF4444" />
          <StatCard label="Warnings" value={stats.severities?.warning || 0} color="#FFA500" />
          <StatCard label="Info" value={stats.severities?.info || 0} color="#4F46E5" />
        </div>
      )}

      {/* Search + Filters */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '24px', flexWrap: 'wrap' }}>
        <input placeholder="Search activity..." value={searchQuery}
          onChange={e => setSearchQuery(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleSearch()}
          style={{ ...inputStyle, flex: 1 }} />
        <select value={filterAction} onChange={e => setFilterAction(e.target.value)} style={{ ...inputStyle, width: 'auto' }}>
          <option value="">All Actions</option>
          {stats && Object.keys(stats.actions || {}).map(a => <option key={a} value={a}>{a}</option>)}
        </select>
        <select value={filterSeverity} onChange={e => setFilterSeverity(e.target.value)} style={{ ...inputStyle, width: 'auto' }}>
          <option value="">All Severities</option>
          <option value="info">Info</option>
          <option value="warning">Warning</option>
          <option value="error">Error</option>
        </select>
      </div>

      {/* Entries */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
        {entries.map((e, i) => (
          <div key={i} style={{ background: '#1A1A1E', borderRadius: '6px', padding: '10px 16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderLeft: `3px solid ${sevColors[e.severity] || '#888'}` }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <span style={{ fontSize: '10px', padding: '2px 6px', borderRadius: '4px', background: (sevColors[e.severity] || '#888') + '22', color: sevColors[e.severity] || '#888' }}>{e.severity}</span>
              <span style={{ fontSize: '13px', fontWeight: 600 }}>{e.action}</span>
              {e.entity_name && <span style={{ fontSize: '12px', color: '#888' }}>{e.entity_type}: {e.entity_name}</span>}
              {e.user_email && <span style={{ fontSize: '11px', color: '#666' }}>by {e.user_email}</span>}
            </div>
            <span style={{ fontSize: '11px', color: '#555' }}>{new Date(e.timestamp).toLocaleString()}</span>
          </div>
        ))}
        {entries.length === 0 && <div style={{ padding: '32px', textAlign: 'center', color: '#666', background: '#1A1A1E', borderRadius: '10px' }}>No activity entries found</div>}
      </div>
    </div>
  );
}

function StatCard({ label, value, color }) {
  return (
    <div style={{ background: '#1A1A1E', borderRadius: '10px', padding: '16px', border: '1px solid #333' }}>
      <div style={{ fontSize: '13px', color: '#888' }}>{label}</div>
      <div style={{ fontSize: '24px', fontWeight: 700, color: color || '#fff', marginTop: '4px' }}>{value}</div>
    </div>
  );
}

const inputStyle = { padding: '8px 12px', background: '#0D0D0F', border: '1px solid #333', borderRadius: '6px', color: '#fff', fontSize: '14px' };

export default ActivityLog;
