import React, { useState, useEffect, useCallback } from 'react';
import webhookService from '../services/webhookService';

function Webhooks() {
  const [subscriptions, setSubscriptions] = useState([]);
  const [events, setEvents] = useState([]);
  const [stats, setStats] = useState(null);
  const [showCreate, setShowCreate] = useState(false);
  const [loading, setLoading] = useState(true);

  const fetchAll = useCallback(async () => {
    try {
      const [subsResp, eventsResp, statsResp] = await Promise.all([
        webhookService.list(),
        webhookService.events(),
        webhookService.stats(),
      ]);
      setSubscriptions(subsResp.data);
      setEvents(eventsResp.data);
      setStats(statsResp.data);
    } catch (err) { console.error('Failed', err); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  if (loading) return <div style={{ padding: '24px', color: '#888' }}>Loading webhooks...</div>;

  return (
    <div style={{ padding: '24px' }}>
      <h1 style={{ fontSize: '28px', fontWeight: 700, margin: '0 0 8px' }}>Webhook Subscriptions</h1>
      <p style={{ color: '#888', marginBottom: '24px' }}>Subscribe external systems to EvolvixOS events</p>

      {stats && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))', gap: '12px', marginBottom: '24px' }}>
          <StatCard label="Subscriptions" value={stats.total_subscriptions} />
          <StatCard label="Active" value={stats.active_subscriptions} color="#22C55E" />
          <StatCard label="Deliveries" value={stats.total_deliveries} />
          <StatCard label="Failed" value={stats.failed_deliveries} color="#EF4444" />
          <StatCard label="Subscribable Events" value={events.length} color="#4F46E5" />
        </div>
      )}

      <button onClick={() => setShowCreate(!showCreate)} style={{ ...btnPrimary, marginBottom: '16px' }}>
        {showCreate ? 'Cancel' : '+ Add Subscription'}
      </button>

      {showCreate && <CreateForm events={events} onCreate={async (data) => { await webhookService.create(data); setShowCreate(false); fetchAll(); }} />}

      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {subscriptions.map(sub => (
          <div key={sub.id} style={{ background: '#1A1A1E', borderRadius: '8px', padding: '16px', border: `1px solid #333`, borderLeft: `3px solid ${sub.active ? '#22C55E' : '#888'}` }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <div>
                <span style={{ fontWeight: 600 }}>{sub.url}</span>
                <span style={{ fontSize: '11px', padding: '2px 6px', borderRadius: '4px', marginLeft: '8px', background: sub.active ? '#22C55E22' : '#88888822', color: sub.active ? '#22C55E' : '#888' }}>
                  {sub.active ? 'Active' : 'Inactive'}
                </span>
              </div>
              <div style={{ display: 'flex', gap: '8px' }}>
                <button onClick={() => webhookService.test(sub.id).then(() => alert('Test sent!'))} style={btnSmall}>Test</button>
                {sub.active ? (
                  <button onClick={async () => { await webhookService.deactivate(sub.id); fetchAll(); }} style={btnSmall}>Disable</button>
                ) : (
                  <button onClick={async () => { await webhookService.activate(sub.id); fetchAll(); }} style={btnSmall}>Enable</button>
                )}
                <button onClick={async () => { await webhookService.delete(sub.id); fetchAll(); }} style={{ ...btnSmall, background: '#5C1A1A' }}>Delete</button>
              </div>
            </div>
            <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap', marginTop: '8px' }}>
              {sub.event_types.map((e, i) => <span key={i} style={{ fontSize: '10px', padding: '2px 6px', background: '#2A2A2E', borderRadius: '4px', color: '#4F46E5' }}>{e}</span>)}
            </div>
            <div style={{ fontSize: '11px', color: '#666', marginTop: '4px' }}>
              Deliveries: {sub.delivery_count} · Failures: {sub.failure_count} · Last: {sub.last_delivery ? new Date(sub.last_delivery).toLocaleString() : 'Never'}
            </div>
          </div>
        ))}
        {subscriptions.length === 0 && <div style={{ padding: '32px', textAlign: 'center', color: '#666', background: '#1A1A1E', borderRadius: '10px' }}>No webhook subscriptions yet</div>}
      </div>
    </div>
  );
}

function CreateForm({ events, onCreate }) {
  const [url, setUrl] = useState('https://');
  const [selectedEvents, setSelectedEvents] = useState([]);
  const [secret, setSecret] = useState('');
  const [description, setDescription] = useState('');

  const toggleEvent = (e) => {
    setSelectedEvents(prev => prev.includes(e) ? prev.filter(x => x !== e) : [...prev, e]);
  };

  return (
    <form onSubmit={ev => { ev.preventDefault(); onCreate({ url, event_types: selectedEvents, secret, description }); }} style={{ background: '#1A1A1E', padding: '20px', borderRadius: '10px', marginBottom: '24px' }}>
      <input placeholder="Webhook URL (https://...)" value={url} onChange={e => setUrl(e.target.value)} style={{ ...inputStyle, width: '100%', marginBottom: '8px' }} required />
      <input placeholder="HMAC Secret (optional)" value={secret} onChange={e => setSecret(e.target.value)} style={{ ...inputStyle, width: '100%', marginBottom: '8px' }} />
      <input placeholder="Description (optional)" value={description} onChange={e => setDescription(e.target.value)} style={{ ...inputStyle, width: '100%', marginBottom: '12px' }} />
      <div style={{ fontSize: '12px', color: '#888', marginBottom: '4px' }}>Select Events:</div>
      <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap', marginBottom: '12px' }}>
        {events.map(e => (
          <button type="button" key={e} onClick={() => toggleEvent(e)} style={selectedEvents.includes(e) ? eventActive : eventBtn}>{e}</button>
        ))}
      </div>
      <button type="submit" disabled={selectedEvents.length === 0} style={btnPrimary}>Create Subscription</button>
    </form>
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
const btnPrimary = { padding: '8px 16px', background: '#4F46E5', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer' };
const btnSmall = { padding: '4px 12px', background: '#2A2A2E', color: '#CCC', border: '1px solid #333', borderRadius: '4px', cursor: 'pointer', fontSize: '12px' };
const eventBtn = { padding: '4px 10px', background: '#1A1A1E', border: '1px solid #333', borderRadius: '4px', color: '#888', cursor: 'pointer', fontSize: '11px' };
const eventActive = { ...eventBtn, background: '#4F46E5', color: '#fff', border: '1px solid #4F46E5' };

export default Webhooks;
