import React, { useState, useEffect, useCallback } from 'react';
import feedbackService from '../services/feedbackService';

function Feedback() {
  const [feedback, setFeedback] = useState([]);
  const [stats, setStats] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({ category: 'bug', rating: 4, title: '', description: '' });

  const fetchAll = useCallback(async () => {
    try {
      const [fResp, sResp] = await Promise.all([
        feedbackService.list(null, null, 30),
        feedbackService.stats(),
      ]);
      setFeedback(fResp.data);
      setStats(sResp.data);
    } catch (err) { console.error(err); }
  }, []);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  const handleSubmit = async () => {
    try {
      await feedbackService.submit(formData);
      setFormData({ category: 'bug', rating: 4, title: '', description: '' });
      setShowForm(false); fetchAll();
    } catch (err) { console.error(err); }
  };

  const handleAction = async (id, action) => {
    try {
      if (action === 'ack') await feedbackService.acknowledge(id);
      if (action === 'dismiss') await feedbackService.dismiss(id);
      fetchAll();
    } catch (err) { console.error(err); }
  };

  const catColors = { bug: '#EF4444', feature_request: '#4F46E5', documentation: '#22C55E', experience: '#FFA500', other: '#888' };

  return (
    <div style={{ padding: '24px' }}>
      <h1 style={{ fontSize: '28px', fontWeight: 700, marginBottom: '4px' }}>💬 Feedback</h1>
      <p style={{ color: '#888', marginBottom: '24px' }}>Developer feedback collection & tracking</p>

      {stats && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(120px, 1fr))', gap: '8px', marginBottom: '20px' }}>
          <Stat label="Total" value={stats.total} />
          <Stat label="Avg Rating" value={`${stats.avg_rating || 0}⭐`} color="#FFA500" />
          <Stat label="Open" value={stats.open || 0} color="#EF4444" />
          <Stat label="Resolved" value={stats.resolved || 0} color="#22C55E" />
        </div>
      )}

      <button onClick={() => setShowForm(!showForm)} style={{ ...btn, background: '#4F46E5', marginBottom: '16px' }}>+ Submit Feedback</button>

      {showForm && (
        <div style={{ ...panel, marginBottom: '16px' }}>
          <select value={formData.category} onChange={e => setFormData({...formData, category: e.target.value})} style={{ ...input, marginRight: '8px' }}>
            <option value="bug">🐛 Bug</option>
            <option value="feature_request">✨ Feature Request</option>
            <option value="documentation">📖 Documentation</option>
            <option value="experience">🎯 Experience</option>
            <option value="other">📦 Other</option>
          </select>
          <select value={formData.rating} onChange={e => setFormData({...formData, rating: parseInt(e.target.value)})} style={{ ...input, marginRight: '8px' }}>
            <option value="5">⭐⭐⭐⭐⭐ Excellent</option>
            <option value="4">⭐⭐⭐⭐ Good</option>
            <option value="3">⭐⭐⭐ Average</option>
            <option value="2">⭐⭐ Poor</option>
            <option value="1">⭐ Terrible</option>
          </select>
          <input value={formData.title} onChange={e => setFormData({...formData, title: e.target.value})} placeholder="Title" style={{ ...input, display: 'block', marginBottom: '8px', width: 'calc(100% - 20px)' }} />
          <textarea value={formData.description} onChange={e => setFormData({...formData, description: e.target.value})} placeholder="Description (optional)" style={{ ...input, display: 'block', width: 'calc(100% - 20px)', minHeight: '60px' }} />
          <button onClick={handleSubmit} style={{ ...btn, background: '#22C55E', marginTop: '8px' }}>Submit</button>
        </div>
      )}

      <div style={{ display: 'grid', gap: '6px' }}>
        {feedback.map(f => (
          <div key={f.id} style={{ ...panel }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <div>
                <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                  <Badge color={catColors[f.category] || '#888'}>{f.category}</Badge>
                  <Badge color={f.status === 'resolved' ? '#22C55E' : f.status === 'acknowledged' ? '#4F46E5' : f.status === 'dismissed' ? '#888' : '#EF4444'}>{f.status}</Badge>
                  <span style={{ color: '#FFA500' }}>{'⭐'.repeat(f.rating)}</span>
                </div>
                <div style={{ fontSize: '14px', fontWeight: 600, marginTop: '4px' }}>{f.title}</div>
                {f.description && <div style={{ fontSize: '12px', color: '#888', marginTop: '2px' }}>{f.description}</div>}
                {f.response && <div style={{ fontSize: '12px', color: '#22C55E', marginTop: '4px' }}>→ {f.response}</div>}
              </div>
              {f.status === 'open' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  <button onClick={() => handleAction(f.id, 'ack')} style={{ ...btnSmall, background: '#4F46E5' }}>Ack</button>
                  <button onClick={() => handleAction(f.id, 'dismiss')} style={{ ...btnSmall, background: '#666' }}>Dismiss</button>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function Stat({ label, value, color }) {
  return (
    <div style={{ background: '#1A1A1E', borderRadius: '8px', padding: '10px', border: '1px solid #333' }}>
      <div style={{ fontSize: '10px', color: '#888' }}>{label}</div>
      <div style={{ fontSize: '18px', fontWeight: 700, color: color || '#fff', marginTop: '2px' }}>{value}</div>
    </div>
  );
}
function Badge({ color, children }) {
  return <span style={{ fontSize: '10px', padding: '2px 6px', borderRadius: '4px', background: color + '22', color, fontWeight: 600 }}>{children}</span>;
}
const panel = { background: '#1A1A1E', borderRadius: '10px', border: '1px solid #333', padding: '12px 16px' };
const btn = { padding: '6px 14px', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '13px' };
const btnSmall = { padding: '4px 10px', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '11px' };
const input = { padding: '6px 10px', background: '#0D0D0F', border: '1px solid #333', borderRadius: '6px', color: '#fff', fontSize: '13px' };

export default Feedback;
