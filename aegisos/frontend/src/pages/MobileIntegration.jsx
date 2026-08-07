import React, { useState, useEffect, useCallback } from 'react';
import mobileService from '../services/mobileService';

function MobileIntegration() {
  const [tab, setTab] = useState('overview');
  const [dashboard, setDashboard] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [features, setFeatures] = useState([]);
  const [quickActions, setQuickActions] = useState([]);
  const [autoRefresh, setAutoRefresh] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const [dash, sess, feat, qa] = await Promise.all([
        mobileService.dashboard(),
        mobileService.listSessions({ limit: 50 }),
        mobileService.features('2.5.3'),
        mobileService.quickActions(),
      ]);
      setDashboard(dash.data || null);
      setSessions(sess.data || []);
      setFeatures(feat.data || []);
      setQuickActions(qa.data || []);
    } catch (err) { console.error(err); }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);
  useEffect(() => {
    if (!autoRefresh) return;
    const i = setInterval(fetchData, 10000);
    return () => clearInterval(i);
  }, [autoRefresh, fetchData]);

  const platformColor = { android: '#22C55E', ios: '#A855F7', web: '#4F46E5' };
  const netColor = { wifi: '#22C55E', '5g': '#4F46E5', '4g': '#FFA500', '3g': '#EF4444' };
  const panel = { background: '#1A1A1E', borderRadius: '10px', border: '1px solid #333', padding: '14px' };
  const btn = { padding: '8px 16px', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '13px', color: '#fff' };

  return (
    <div style={{ padding: '24px' }}>
      <h1 style={{ fontSize: '28px', fontWeight: 700, marginBottom: '4px' }}>📱 Mobile Integration</h1>
      <p style={{ color: '#888', marginBottom: '12px' }}>Verdis Android wallet × EvolvixOS integration hub</p>

      <div style={{ display: 'flex', gap: '4px', marginBottom: '12px', flexWrap: 'wrap' }}>
        {['overview', 'sessions', 'features', 'actions'].map(t => (
          <button key={t} onClick={() => setTab(t)} style={{ ...btn, background: tab === t ? '#4F46E5' : '#1A1A1E', textTransform: 'capitalize' }}>{t}</button>
        ))}
        <button onClick={() => setAutoRefresh(!autoRefresh)} style={{ ...btn, background: autoRefresh ? '#22C55E' : '#1A1A1E' }}>{autoRefresh ? '⏸ Auto' : '▶ Auto'}</button>
      </div>

      {tab === 'overview' && dashboard && (
        <div style={{ display: 'grid', gap: '12px' }}>
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            {[
              { l: 'Sessions', v: dashboard.stats?.total_sessions || 0 },
              { l: 'Android', v: dashboard.stats?.android_sessions || 0 },
              { l: 'iOS', v: dashboard.stats?.ios_sessions || 0 },
              { l: 'Biometric', v: dashboard.stats?.biometric_enabled || 0 },
              { l: 'Unique Wallets', v: dashboard.stats?.unique_wallets || 0 },
              { l: 'Total Syncs', v: dashboard.stats?.total_syncs || 0 },
              { l: 'Unread', v: dashboard.stats?.unread_notifications || 0 },
              { l: 'Features', v: dashboard.stats?.total_features || 0 },
            ].map(s => (
              <div key={s.l} style={{ ...panel, flex: '1 1 100px', textAlign: 'center' }}>
                <div style={{ fontSize: '10px', color: '#888' }}>{s.l}</div>
                <div style={{ fontSize: '16px', fontWeight: 700 }}>{s.v}</div>
              </div>
            ))}
          </div>

          {/* Recent Sessions */}
          <div style={panel}>
            <div style={{ fontSize: '14px', fontWeight: 600, marginBottom: '8px' }}>Recent Sessions</div>
            {dashboard.recent_sessions?.map((s, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', borderBottom: '1px solid #222', fontSize: '12px' }}>
                <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                  <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: platformColor[s.platform] || '#888' }} />
                  <span>{s.wallet_address?.slice(0, 12)}...</span>
                  <span style={{ fontSize: '9px', color: '#888' }}>v{s.app_version}</span>
                </div>
                <div style={{ display: 'flex', gap: '8px', fontSize: '10px', color: '#888' }}>
                  <span style={{ color: netColor[s.network_type] || '#888' }}>{s.network_type}</span>
                  <span>🔋{s.battery_level}%</span>
                  {s.biometric_enabled && <span>🔐</span>}
                  <span>{new Date(s.last_seen).toLocaleTimeString()}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {tab === 'sessions' && (
        <div style={{ display: 'grid', gap: '6px' }}>
          {sessions.map((s, i) => (
            <div key={i} style={panel}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                  <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: platformColor[s.platform] || '#888' }} />
                  <span style={{ fontSize: '13px', fontWeight: 600 }}>{s.wallet_address?.slice(0, 14)}...</span>
                </div>
                <span style={{ fontSize: '9px', padding: '2px 6px', borderRadius: '4px', background: '#4F46E522', color: '#4F46E5' }}>{s.platform}</span>
              </div>
              <div style={{ display: 'flex', gap: '12px', fontSize: '11px', marginTop: '4px', color: '#888', flexWrap: 'wrap' }}>
                <span>Device: {s.device_id?.slice(0, 12)}...</span>
                <span>Version: v{s.app_version}</span>
                <span style={{ color: netColor[s.network_type] || '#888' }}>Network: {s.network_type}</span>
                <span>🔋 {s.battery_level}%</span>
                <span>Language: {s.language}</span>
                {s.biometric_enabled && <span>🔐 Biometric</span>}
                {s.pin_enabled && <span>🔑 PIN</span>}
                <span>Features: {s.features_enabled?.length || 0}</span>
                <span>Last seen: {new Date(s.last_seen).toLocaleString()}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {tab === 'features' && (
        <div style={{ display: 'grid', gap: '6px' }}>
          {features.map((f, i) => (
            <div key={i} style={panel}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                  <span style={{ fontSize: '18px' }}>{f.icon}</span>
                  <div>
                    <div style={{ fontSize: '13px', fontWeight: 600 }}>{f.name}</div>
                    <div style={{ fontSize: '11px', color: '#888' }}>{f.description}</div>
                  </div>
                </div>
                <div style={{ display: 'flex', gap: '4px' }}>
                  {f.requires_auth && <span style={{ fontSize: '9px', padding: '2px 6px', borderRadius: '4px', background: '#4F46E522', color: '#4F46E5' }}>Auth</span>}
                  {f.requires_biometric && <span style={{ fontSize: '9px', padding: '2px 6px', borderRadius: '4px', background: '#A855F722', color: '#A855F7' }}>Biometric</span>}
                  <span style={{ fontSize: '9px', padding: '2px 6px', borderRadius: '4px', background: f.available ? '#22C55E22' : '#88822', color: f.available ? '#22C55E' : '#888' }}>{f.available ? 'available' : 'unavailable'}</span>
                </div>
              </div>
              <div style={{ fontSize: '10px', color: '#888', marginTop: '4px' }}>
                Min version: {f.min_app_version} | API: {f.api_base}
              </div>
            </div>
          ))}
        </div>
      )}

      {tab === 'actions' && (
        <div style={{ display: 'grid', gap: '6px', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))' }}>
          {quickActions.map((a, i) => (
            <div key={i} style={panel}>
              <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                <span style={{ fontSize: '20px' }}>{a.icon}</span>
                <div>
                  <div style={{ fontSize: '13px', fontWeight: 600 }}>{a.label}</div>
                  <div style={{ fontSize: '10px', color: '#888' }}>{a.feature}</div>
                </div>
              </div>
              <div style={{ fontSize: '9px', color: '#4F46E5', marginTop: '4px' }}>{a.api_endpoint}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default MobileIntegration;
