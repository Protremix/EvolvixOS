import React, { useState, useEffect, useCallback } from 'react';
import notificationService from '../services/notificationService';

function NotificationCenter() {
  const [notifications, setNotifications] = useState([]);
  const [dashboard, setDashboard] = useState(null);
  const [filter, setFilter] = useState('all'); // all, unread, by type
  const [autoRefresh, setAutoRefresh] = useState(false);

  const userAddr = '0xverdis';

  const fetchData = useCallback(async () => {
    try {
      const [dash, notifs] = await Promise.all([
        notificationService.dashboard(userAddr),
        notificationService.list({ user_address: userAddr, limit: 50 }),
      ]);
      setDashboard(dash.data || null);
      setNotifications(notifs.data || []);
    } catch (err) { console.error(err); }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);
  useEffect(() => {
    if (!autoRefresh) return;
    const i = setInterval(fetchData, 5000);
    return () => clearInterval(i);
  }, [autoRefresh, fetchData]);

  const handleMarkRead = async (id) => {
    try { await notificationService.markRead(id); fetchData(); } catch (e) { console.error(e); }
  };

  const handleMarkAllRead = async () => {
    try { await notificationService.markAllRead(userAddr); fetchData(); } catch (e) { console.error(e); }
  };

  const handleDelete = async (id) => {
    try { await notificationService.delete(id); fetchData(); } catch (e) { console.error(e); }
  };

  const handleClearRead = async () => {
    try { await notificationService.clearRead(userAddr); fetchData(); } catch (e) { console.error(e); }
  };

  const sevColor = { info: '#4F46E5', success: '#22C55E', warning: '#FFA500', error: '#EF4444', critical: '#EF4444' };
  const typeIcons = { transaction: '💸', governance: '🏛️', security: '🔒', system: '⚙️', bridge: '🌉', validator: '⚡', tokenomics: '💰', deployment: '🚀', agent: '🤖', plugin: '🧩' };
  const panel = { background: '#1A1A1E', borderRadius: '10px', border: '1px solid #333', padding: '14px' };
  const btn = { padding: '8px 16px', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '13px', color: '#fff' };

  const filtered = filter === 'all' ? notifications : filter === 'unread' ? notifications.filter(n => !n.read) : notifications.filter(n => n.type === filter);

  return (
    <div style={{ padding: '24px' }}>
      <h1 style={{ fontSize: '28px', fontWeight: 700, marginBottom: '4px' }}>🔔 Notifications</h1>
      <p style={{ color: '#888', marginBottom: '12px' }}>Real-time alerts across the ecosystem</p>

      <div style={{ display: 'flex', gap: '4px', marginBottom: '12px', flexWrap: 'wrap' }}>
        <button onClick={() => setFilter('all')} style={{ ...btn, background: filter === 'all' ? '#4F46E5' : '#1A1A1E' }}>All</button>
        <button onClick={() => setFilter('unread')} style={{ ...btn, background: filter === 'unread' ? '#4F46E5' : '#1A1A1E' }}>Unread {dashboard?.unread_count > 0 ? `(${dashboard.unread_count})` : ''}</button>
        {['transaction', 'governance', 'security', 'system', 'bridge', 'validator', 'tokenomics'].map(t => (
          <button key={t} onClick={() => setFilter(t)} style={{ ...btn, background: filter === t ? '#4F46E5' : '#1A1A1E', fontSize: '11px', textTransform: 'capitalize' }}>{t}</button>
        ))}
        <button onClick={() => setAutoRefresh(!autoRefresh)} style={{ ...btn, background: autoRefresh ? '#22C55E' : '#1A1A1E' }}>{autoRefresh ? '⏸ Auto' : '▶ Auto'}</button>
        <button onClick={handleMarkAllRead} style={{ ...btn, background: '#1A1A1E' }}>✓ Mark All Read</button>
        <button onClick={handleClearRead} style={{ ...btn, background: '#1A1A1E' }}>🗑 Clear Read</button>
      </div>

      {dashboard && (
        <div style={{ display: 'flex', gap: '8px', marginBottom: '12px', flexWrap: 'wrap' }}>
          {[{ l: 'Total', v: dashboard.stats?.total || 0 }, { l: 'Unread', v: dashboard.unread_count || 0 }, { l: 'Read', v: dashboard.stats?.read || 0 }].map(s => (
            <div key={s.l} style={{ ...panel, flex: '1 1 80px', textAlign: 'center' }}>
              <div style={{ fontSize: '10px', color: '#888' }}>{s.l}</div>
              <div style={{ fontSize: '16px', fontWeight: 700 }}>{s.v}</div>
            </div>
          ))}
        </div>
      )}

      <div style={{ display: 'grid', gap: '6px' }}>
        {filtered.map((n, i) => (
          <div key={i} style={{ ...panel, borderLeft: `3px solid ${sevColor[n.severity] || '#888'}`, opacity: n.read ? 0.6 : 1 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
              <div style={{ display: 'flex', gap: '8px', alignItems: 'start' }}>
                <span style={{ fontSize: '16px' }}>{typeIcons[n.type] || '📢'}</span>
                <div>
                  <div style={{ fontSize: '13px', fontWeight: n.read ? 400 : 600 }}>{n.title}</div>
                  <div style={{ fontSize: '11px', color: '#888', marginTop: '2px' }}>{n.message}</div>
                </div>
              </div>
              <div style={{ display: 'flex', gap: '4px', alignItems: 'center' }}>
                <span style={{ fontSize: '9px', padding: '2px 6px', borderRadius: '4px', background: (sevColor[n.severity] || '#888') + '22', color: sevColor[n.severity] || '#888' }}>{n.severity}</span>
                {!n.read && <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#4F46E5' }} />}
              </div>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '8px' }}>
              <div style={{ fontSize: '10px', color: '#666' }}>{new Date(n.created).toLocaleString()}</div>
              <div style={{ display: 'flex', gap: '8px' }}>
                {!n.read && <button onClick={() => handleMarkRead(n.id)} style={{ ...btn, background: '#1A1A1E', fontSize: '10px', padding: '2px 8px' }}>Mark Read</button>}
                <button onClick={() => handleDelete(n.id)} style={{ ...btn, background: '#1A1A1E', fontSize: '10px', padding: '2px 8px' }}>🗑</button>
              </div>
            </div>
          </div>
        ))}
        {filtered.length === 0 && <div style={{ fontSize: '12px', color: '#888', textAlign: 'center', padding: '20px' }}>No notifications</div>}
      </div>
    </div>
  );
}

export default NotificationCenter;
