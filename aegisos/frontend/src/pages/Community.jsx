import React, { useState, useEffect, useCallback } from 'react';
import communityService from '../services/communityService';

function Community() {
  const [tab, setTab] = useState('overview');
  const [dashboard, setDashboard] = useState(null);
  const [feedback, setFeedback] = useState([]);
  const [features, setFeatures] = useState([]);
  const [members, setMembers] = useState([]);
  const [events, setEvents] = useState([]);
  const [badges, setBadges] = useState([]);
  const [usability, setUsability] = useState([]);

  const fetchData = useCallback(async () => {
    try {
      const [dash, fb, fr, mem, evt, bdg, us] = await Promise.all([
        communityService.dashboard(),
        communityService.feedback({ limit: 20 }),
        communityService.features({ limit: 20 }),
        communityService.members(20),
        communityService.events(),
        communityService.badges(),
        communityService.usability(),
      ]);
      setDashboard(dash.data || null);
      setFeedback(fb.data || []);
      setFeatures(fr.data || []);
      setMembers(mem.data || []);
      setEvents(evt.data || []);
      setBadges(bdg.data || []);
      setUsability(us.data || []);
    } catch (err) { console.error(err); }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleVoteFeature = async (id) => {
    try { await communityService.voteFeature(id, ''); fetchData(); } catch (e) { console.error(e); }
  };

  const handleVoteFeedback = async (id) => {
    try { await communityService.voteFeedback(id); fetchData(); } catch (e) { console.error(e); }
  };

  const panel = { background: '#1A1A1E', borderRadius: '10px', border: '1px solid #333', padding: '14px' };
  const btn = { padding: '6px 12px', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '12px', color: '#fff' };
  const typeColor = { bug: '#EF4444', feature_request: '#4F46E5', improvement: '#FFA500', praise: '#22C55E', question: '#3B82F6' };
  const sevColor = { critical: '#EF4444', high: '#F97316', medium: '#FFA500', low: '#4F46E5', info: '#888' };
  const eventColor = { upcoming: '#22C55E', live: '#EF4444', ended: '#888', cancelled: '#666' };

  return (
    <div style={{ padding: '24px' }}>
      <h1 style={{ fontSize: '28px', fontWeight: 700, marginBottom: '4px' }}>👥 Community & UX</h1>
      <p style={{ color: '#888', marginBottom: '12px' }}>Feedback, feature requests, members, events, and usability</p>

      {dashboard && (
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '12px' }}>
          {[
            { l: 'Feedback', v: dashboard.feedback_stats?.total || 0 },
            { l: 'Features', v: dashboard.feature_requests || 0 },
            { l: 'Members', v: dashboard.total_members || 0 },
            { l: 'Events', v: dashboard.total_events || 0 },
            { l: 'Upcoming', v: dashboard.upcoming_events || 0 },
            { l: 'Badges', v: dashboard.total_badges || 0 },
            { l: 'Avg Rating', v: dashboard.feedback_stats?.avg_rating || 0 },
            { l: 'Satisfaction', v: dashboard.usability?.avg_satisfaction || 0 },
          ].map(s => (
            <div key={s.l} style={{ ...panel, flex: '1 1 80px', textAlign: 'center' }}>
              <div style={{ fontSize: '10px', color: '#888' }}>{s.l}</div>
              <div style={{ fontSize: '16px', fontWeight: 700 }}>{s.v}</div>
            </div>
          ))}
        </div>
      )}

      <div style={{ display: 'flex', gap: '4px', marginBottom: '12px', flexWrap: 'wrap' }}>
        {['overview', 'feedback', 'features', 'members', 'events', 'badges'].map(t => (
          <button key={t} onClick={() => setTab(t)} style={{ ...btn, background: tab === t ? '#4F46E5' : '#1A1A1E', textTransform: 'capitalize' }}>{t}</button>
        ))}
      </div>

      {tab === 'overview' && dashboard && (
        <div style={{ display: 'grid', gap: '12px' }}>
          {/* Top members */}
          <div style={panel}>
            <div style={{ fontSize: '14px', fontWeight: 600, marginBottom: '8px' }}>🏆 Top Members</div>
            {dashboard.top_members?.map((m, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', borderBottom: '1px solid #222', fontSize: '12px' }}>
                <div>#{i + 1} {m.username || m.address.slice(0, 10)}</div>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <span style={{ color: '#4F46E5' }}>⭐ {m.points} pts</span>
                  <span style={{ color: '#FFA500' }}>Lvl {m.level}</span>
                  <span style={{ color: '#22C55E' }}>{m.badges?.length || 0} 🏅</span>
                </div>
              </div>
            ))}
          </div>

          {/* Top features */}
          <div style={panel}>
            <div style={{ fontSize: '14px', fontWeight: 600, marginBottom: '8px' }}>💡 Top Feature Requests</div>
            {dashboard.top_features?.map((f, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', borderBottom: '1px solid #222', fontSize: '12px' }}>
                <span>{f.title}</span>
                <span style={{ color: '#4F46E5' }}>👍 {f.votes}</span>
              </div>
            ))}
          </div>

          {/* Usability summary */}
          {dashboard.usability && (
            <div style={panel}>
              <div style={{ fontSize: '14px', fontWeight: 600, marginBottom: '8px' }}>📊 Usability Summary</div>
              <div style={{ fontSize: '12px', color: '#888' }}>
                <div>Pages tracked: {dashboard.usability.total_pages}</div>
                <div>Total visits: {dashboard.usability.total_visits}</div>
                <div>Avg duration: {dashboard.usability.avg_duration}s</div>
                <div>Avg bounce rate: {dashboard.usability.avg_bounce_rate}%</div>
                <div>Avg satisfaction: {dashboard.usability.avg_satisfaction}/5</div>
                <div>Best page: <b style={{ color: '#22C55E' }}>{dashboard.usability.best_page}</b></div>
                <div>Worst page: <b style={{ color: '#FFA500' }}>{dashboard.usability.worst_page}</b></div>
              </div>
            </div>
          )}
        </div>
      )}

      {tab === 'feedback' && (
        <div style={{ display: 'grid', gap: '6px' }}>
          {feedback.map((f, i) => (
            <div key={i} style={{ ...panel, borderLeft: `3px solid ${typeColor[f.type] || '#888'}` }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <div style={{ fontSize: '13px', fontWeight: 600 }}>{f.title}</div>
                <div style={{ display: 'flex', gap: '4px' }}>
                  <span style={{ fontSize: '9px', padding: '2px 6px', borderRadius: '4px', background: (typeColor[f.type] || '#888') + '22', color: typeColor[f.type] || '#888' }}>{f.type}</span>
                  <span style={{ fontSize: '9px', padding: '2px 6px', borderRadius: '4px', background: (sevColor[f.severity] || '#888') + '22', color: sevColor[f.severity] || '#888' }}>{f.severity}</span>
                  <button onClick={() => handleVoteFeedback(f.id)} style={{ ...btn, background: '#1A1A1E', fontSize: '10px' }}>👍 {f.votes}</button>
                </div>
              </div>
              <div style={{ fontSize: '11px', color: '#888', marginTop: '4px' }}>{f.description}</div>
              <div style={{ fontSize: '10px', color: '#666', marginTop: '4px' }}>Page: {f.page} | Rating: {'⭐'.repeat(f.rating)} | Status: {f.status}</div>
            </div>
          ))}
        </div>
      )}

      {tab === 'features' && (
        <div style={{ display: 'grid', gap: '6px' }}>
          {features.map((f, i) => (
            <div key={i} style={panel}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <div style={{ fontSize: '13px', fontWeight: 600 }}>{f.title}</div>
                <button onClick={() => handleVoteFeature(f.id)} style={{ ...btn, background: '#4F46E5', fontSize: '10px' }}>👍 {f.votes}</button>
              </div>
              <div style={{ fontSize: '11px', color: '#888', marginTop: '4px' }}>{f.description}</div>
              <div style={{ fontSize: '10px', color: '#666', marginTop: '4px' }}>
                Category: {f.category} | Priority: {f.priority} | Effort: {f.estimated_effort || 'N/A'} | Status: {f.status}
                {f.target_phase && ` | Target: ${f.target_phase}`}
              </div>
              {f.comments?.length > 0 && <div style={{ fontSize: '10px', color: '#4F46E5', marginTop: '4px' }}>💬 {f.comments.length} comments</div>}
            </div>
          ))}
        </div>
      )}

      {tab === 'members' && (
        <div style={{ display: 'grid', gap: '4px' }}>
          {members.map((m, i) => (
            <div key={i} style={panel}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <div style={{ fontSize: '13px', fontWeight: 600 }}>#{i + 1} {m.username || m.address.slice(0, 12)}</div>
                <div style={{ display: 'flex', gap: '8px', fontSize: '12px' }}>
                  <span style={{ color: '#4F46E5' }}>⭐ {m.points}</span>
                  <span style={{ color: '#FFA500' }}>Lvl {m.level}</span>
                  <span style={{ color: '#22C55E' }}>{m.badges?.length || 0} 🏅</span>
                </div>
              </div>
              <div style={{ fontSize: '10px', color: '#888', marginTop: '4px' }}>
                Feedback: {m.feedback_count} | Votes: {m.feature_votes} | Events: {m.event_attendance}
                {m.badges?.length > 0 && <div style={{ color: '#4F46E5' }}>Badges: {m.badges.join(', ')}</div>}
              </div>
            </div>
          ))}
        </div>
      )}

      {tab === 'events' && (
        <div style={{ display: 'grid', gap: '6px' }}>
          {events.map((e, i) => (
            <div key={i} style={{ ...panel, borderLeft: `3px solid ${eventColor[e.status] || '#888'}` }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <div style={{ fontSize: '13px', fontWeight: 600 }}>{e.name}</div>
                <div style={{ display: 'flex', gap: '4px' }}>
                  <span style={{ fontSize: '9px', padding: '2px 6px', borderRadius: '4px', background: '#4F46E522', color: '#4F46E5' }}>{e.type}</span>
                  <span style={{ fontSize: '9px', padding: '2px 6px', borderRadius: '4px', background: (eventColor[e.status] || '#888') + '22', color: eventColor[e.status] || '#888' }}>{e.status}</span>
                </div>
              </div>
              <div style={{ fontSize: '11px', color: '#888', marginTop: '4px' }}>{e.description}</div>
              <div style={{ fontSize: '10px', color: '#666', marginTop: '4px' }}>
                Registered: {e.registered}/{e.max_participants || '∞'} | Reward: {e.reward_points} pts
                {e.start_time && ` | Start: ${new Date(e.start_time).toLocaleDateString()}`}
              </div>
            </div>
          ))}
        </div>
      )}

      {tab === 'badges' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '8px' }}>
          {badges.map((b, i) => (
            <div key={i} style={panel}>
              <div style={{ fontSize: '24px', marginBottom: '4px' }}>{b.icon}</div>
              <div style={{ fontSize: '13px', fontWeight: 600 }}>{b.name}</div>
              <div style={{ fontSize: '11px', color: '#888' }}>{b.description}</div>
              <div style={{ fontSize: '10px', color: '#4F46E5', marginTop: '4px' }}>+{b.points} pts</div>
              <div style={{ fontSize: '10px', color: '#666' }}>{b.criteria}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default Community;
