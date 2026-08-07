import React, { useState, useEffect, useCallback } from 'react';
import backupService from '../services/backupService';

function Backups() {
  const [history, setHistory] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);

  const fetchAll = useCallback(async () => {
    try {
      const [histResp, statsResp] = await Promise.all([
        backupService.history(20),
        backupService.stats(),
      ]);
      setHistory(histResp.data);
      setStats(statsResp.data);
    } catch (err) { console.error('Failed', err); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  const handleCreate = async () => {
    setCreating(true);
    try {
      await backupService.create(`Manual backup ${new Date().toLocaleString()}`);
      fetchAll();
    } catch (err) { console.error(err); }
    finally { setCreating(false); }
  };

  if (loading) return <div style={{ padding: '24px', color: '#888' }}>Loading backups...</div>;

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '24px' }}>
        <div>
          <h1 style={{ fontSize: '28px', fontWeight: 700, margin: '0 0 4px' }}>Backup & Restore</h1>
          <p style={{ color: '#888' }}>Export and restore full system state</p>
        </div>
        <button onClick={handleCreate} disabled={creating} style={btnPrimary}>
          {creating ? 'Creating...' : '+ Create Backup'}
        </button>
      </div>

      {stats && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))', gap: '12px', marginBottom: '24px' }}>
          <StatCard label="Total Backups" value={stats.total_backups} />
          <StatCard label="Last Backup" value={stats.last_backup ? new Date(stats.last_backup.timestamp).toLocaleDateString() : 'Never'} />
          {stats.last_backup && <StatCard label="Last Size" value={`${(stats.last_backup.size_bytes / 1024).toFixed(1)} KB`} color="#4F46E5" />}
        </div>
      )}

      <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
        {history.map(b => (
          <div key={b.id} style={{ background: '#1A1A1E', borderRadius: '6px', padding: '12px 16px', display: 'flex', justifyContent: 'space-between' }}>
            <div>
              <span style={{ fontSize: '13px', fontWeight: 600 }}>{b.description || b.id}</span>
              <div style={{ fontSize: '11px', color: '#666' }}>{new Date(b.timestamp).toLocaleString()} · {(b.size_bytes / 1024).toFixed(1)} KB</div>
            </div>
            <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap', justifyContent: 'flex-end' }}>
              {Object.entries(b.entity_counts || {}).filter(([k, v]) => v > 0).map(([entity, count]) => (
                <span key={entity} style={{ fontSize: '10px', padding: '1px 6px', background: '#2A2A2E', borderRadius: '3px', color: '#4F46E5' }}>
                  {entity}: {count}
                </span>
              ))}
            </div>
          </div>
        ))}
        {history.length === 0 && <div style={{ padding: '32px', textAlign: 'center', color: '#666', background: '#1A1A1E', borderRadius: '10px' }}>No backups yet</div>}
      </div>
    </div>
  );
}

function StatCard({ label, value, color }) {
  return (
    <div style={{ background: '#1A1A1E', borderRadius: '10px', padding: '16px', border: '1px solid #333' }}>
      <div style={{ fontSize: '13px', color: '#888' }}>{label}</div>
      <div style={{ fontSize: '20px', fontWeight: 700, color: color || '#fff', marginTop: '4px' }}>{value}</div>
    </div>
  );
}

const btnPrimary = { padding: '8px 16px', background: '#4F46E5', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer' };

export default Backups;
