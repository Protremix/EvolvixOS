import React, { useState, useEffect, useCallback } from 'react';
import collabMonitorService from '../services/collabMonitorService';

function CollabMonitor() {
  const [tab, setTab] = useState('collab');
  const [patterns, setPatterns] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [stats, setStats] = useState(null);
  const [feed, setFeed] = useState(null);
  const [sysStats, setSysStats] = useState(null);
  const [selectedSession, setSelectedSession] = useState(null);
  const [creating, setCreating] = useState(false);

  const fetchAll = useCallback(async () => {
    try {
      const [pResp, sResp, stResp, fResp, ssResp] = await Promise.all([
        collabMonitorService.patterns(),
        collabMonitorService.listSessions(),
        collabMonitorService.collabStats(),
        collabMonitorService.liveFeed(20),
        collabMonitorService.systemStats(),
      ]);
      setPatterns(pResp.data);
      setSessions(sResp.data);
      setStats(stResp.data);
      setFeed(fResp.data);
      setSysStats(ssResp.data);
    } catch (err) { console.error(err); }
  }, []);

  useEffect(() => {
    fetchAll();
    const interval = setInterval(fetchAll, 5000); // Auto-refresh every 5s
    return () => clearInterval(interval);
  }, [fetchAll]);

  const handleCreate = async (pattern, name) => {
    setCreating(true);
    try {
      await collabMonitorService.createSession({ name, pattern });
      fetchAll();
    } catch (err) { console.error(err); }
    finally { setCreating(false); }
  };

  const handleSimulate = async (id) => {
    try { await collabMonitorService.simulateSession(id); fetchAll(); }
    catch (err) { console.error(err); }
  };

  const handleExecute = async (id, useVerdis = true) => {
    try { await collabMonitorService.executeSession(id, useVerdis); fetchAll(); }
    catch (err) { console.error(err); }
  };

  return (
    <div style={{ padding: '24px' }}>
      <h1 style={{ fontSize: '28px', fontWeight: 700, marginBottom: '4px' }}>🔗 Collaboration & Monitor</h1>
      <p style={{ color: '#888', marginBottom: '24px' }}>Agent collaboration sessions and real-time monitoring</p>

      {/* System Stats Bar */}
      {sysStats && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(110px, 1fr))', gap: '8px', marginBottom: '20px' }}>
          <Stat label="Tasks Running" value={sysStats.tasks_running} color="#FFA500" />
          <Stat label="Completed" value={sysStats.tasks_completed} color="#22C55E" />
          <Stat label="Failed" value={sysStats.tasks_failed} color="#EF4444" />
          <Stat label="Collabs Active" value={sysStats.collaborations_active} color="#4F46E5" />
          <Stat label="Collabs Done" value={sysStats.collaborations_completed} color="#22C55E" />
          <Stat label="Events Buffered" value={sysStats.events_buffered} />
          <Stat label="Tokens Used" value={sysStats.total_tokens_used} />
        </div>
      )}

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '4px', marginBottom: '16px' }}>
        {[
          { key: 'collab', label: 'Collaboration' },
          { key: 'sessions', label: 'Sessions' },
          { key: 'live', label: 'Live Feed' },
          { key: 'patterns', label: 'Patterns' },
        ].map(t => (
          <button key={t.key} onClick={() => setTab(t.key)} style={{
            padding: '6px 16px', border: '1px solid #333', borderRadius: '6px 6px 0 0',
            background: tab === t.key ? '#4F46E5' : '#1A1A1E', color: tab === t.key ? '#fff' : '#888',
            cursor: 'pointer', fontSize: '13px',
          }}>{t.label}</button>
        ))}
      </div>

      {/* Patterns Tab */}
      {tab === 'patterns' && (
        <div style={{ display: 'grid', gap: '12px' }}>
          {patterns.map(p => (
            <div key={p.key} style={{ ...panel }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                <div>
                  <div style={{ fontSize: '15px', fontWeight: 600 }}>{p.name}</div>
                  <div style={{ fontSize: '12px', color: '#888', marginTop: '2px' }}>{p.description}</div>
                  <div style={{ display: 'flex', gap: '4px', marginTop: '8px' }}>
                    {p.agents.map(a => <Badge key={a} color="#4F46E5">{a}</Badge>)}
                  </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: '12px', color: '#888' }}>{p.step_count} steps</div>
                  <button onClick={() => handleCreate(p.key, `${p.name} Session`)} disabled={creating} style={{ ...btn, marginTop: '6px' }}>
                    Create Session
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Sessions Tab */}
      {tab === 'sessions' && (
        <div style={{ display: 'grid', gap: '8px' }}>
          {sessions.length === 0 && <div style={{ color: '#888' }}>No collaboration sessions yet. Create one from Patterns tab.</div>}
          {sessions.map(s => (
            <div key={s.id} style={{ ...panel, cursor: 'pointer' }} onClick={() => setSelectedSession(s)}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <div>
                  <div style={{ fontSize: '14px', fontWeight: 600 }}>{s.name}</div>
                  <div style={{ fontSize: '11px', color: '#888' }}>{s.pattern} · {s.agents_involved?.length || 0} agents</div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <Badge color={s.status === 'completed' ? '#22C55E' : s.status === 'running' ? '#FFA500' : '#888'}>{s.status}</Badge>
                  {s.status === 'pending' && (
                    <div style={{ display: 'flex', gap: '4px' }}>
                      <button onClick={(e) => { e.stopPropagation(); handleSimulate(s.id); }} style={{ ...btn, background: '#666' }}>▶ Simulate</button>
                      <button onClick={(e) => { e.stopPropagation(); handleExecute(s.id, true); }} style={{ ...btn, background: '#22C55E' }}>⚡ Execute Real</button>
                    </div>
                  )}
                </div>
              </div>
              {selectedSession?.id === s.id && (
                <div style={{ marginTop: '12px', paddingTop: '12px', borderTop: '1px solid #333' }}>
                  {s.steps.map((step, i) => (
                    <div key={step.id} style={{ display: 'flex', gap: '8px', padding: '4px 0', alignItems: 'center' }}>
                      <span style={{ fontSize: '10px', color: '#666', minWidth: '20px' }}>#{i+1}</span>
                      <Badge color="#4F46E5">{step.agent_name}</Badge>
                      <span style={{ fontSize: '11px', color: '#888' }}>{step.task_type}</span>
                      <Badge color={step.status === 'completed' ? '#22C55E' : step.status === 'running' ? '#FFA500' : '#666'}>{step.status}</Badge>
                      {step.score && <span style={{ fontSize: '12px', fontWeight: 600, color: step.score >= 8 ? '#22C55E' : '#FFA500' }}>{step.score}/10</span>}
                      {step.verdict && <Badge color={step.verdict === 'GO' ? '#22C55E' : '#EF4444'}>{step.verdict}</Badge>}
                    </div>
                  ))}
                  {s.final_result?.avg_score != null && (
                    <div style={{ marginTop: '8px', fontSize: '13px', color: '#4F46E5' }}>
                      Final: {s.final_result.avg_score}/10 · {s.final_result.total_findings} findings · {s.final_result.overall_verdict}
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Collaboration Tab (patterns + sessions combined view) */}
      {tab === 'collab' && (
        <div>
          {stats && (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(120px, 1fr))', gap: '8px', marginBottom: '16px' }}>
              <Stat label="Total Sessions" value={stats.total_sessions} />
              <Stat label="Completed" value={stats.completed} color="#22C55E" />
              <Stat label="Running" value={stats.running} color="#FFA500" />
              <Stat label="Patterns" value={stats.patterns_available} color="#4F46E5" />
            </div>
          )}
          <div style={{ fontSize: '14px', fontWeight: 600, marginBottom: '8px' }}>Quick Start</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginBottom: '16px' }}>
            {patterns.map(p => (
              <button key={p.key} onClick={() => handleCreate(p.key, `${p.name}`)} disabled={creating} style={{
                padding: '8px 14px', background: '#2A2A2E', border: '1px solid #333', borderRadius: '8px',
                cursor: 'pointer', fontSize: '12px', color: '#CCC',
              }}>
                {p.name} ({p.agents.length} agents)
              </button>
            ))}
          </div>
          <div style={{ fontSize: '14px', fontWeight: 600, marginBottom: '8px' }}>Recent Sessions</div>
          {sessions.slice(0, 5).map(s => (
            <div key={s.id} style={{ ...panel, marginBottom: '6px', padding: '10px 14px', display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ fontSize: '13px' }}>{s.name}</span>
              <div style={{ display: 'flex', gap: '6px' }}>
                <Badge color="#4F46E5">{s.pattern}</Badge>
                <Badge color={s.status === 'completed' ? '#22C55E' : '#888'}>{s.status}</Badge>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Live Feed Tab */}
      {tab === 'live' && feed && (
        <div>
          <div style={{ fontSize: '14px', fontWeight: 600, marginBottom: '8px' }}>
            Live Event Feed ({feed.event_count} total events)
          </div>
          {feed.events.length === 0 && <div style={{ color: '#888' }}>No events yet. Events appear here in real-time.</div>}
          {feed.events.map(e => (
            <div key={e.id} style={{ ...panel, padding: '8px 14px', marginBottom: '4px', display: 'flex', gap: '8px', alignItems: 'center' }}>
              <span style={{ fontSize: '9px', color: '#555', minWidth: '70px' }}>{new Date(e.timestamp).toLocaleTimeString()}</span>
              <Badge color={
                e.severity === 'success' ? '#22C55E' :
                e.severity === 'error' ? '#EF4444' :
                e.severity === 'warning' ? '#FFA500' : '#4F46E5'
              }>{e.type}</Badge>
              <span style={{ fontSize: '11px', color: '#888', minWidth: '100px' }}>{e.source}</span>
              <span style={{ fontSize: '13px', color: '#CCC', flex: 1 }}>{e.message}</span>
            </div>
          ))}
        </div>
      )}
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
const btn = { padding: '6px 12px', background: '#4F46E5', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '12px' };

export default CollabMonitor;
