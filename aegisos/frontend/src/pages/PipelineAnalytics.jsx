import React, { useState, useEffect, useCallback } from 'react';
import analyticsService from '../services/pipelineAnalyticsService';

function PipelineAnalytics() {
  const [analytics, setAnalytics] = useState(null);
  const [schedules, setSchedules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [tab, setTab] = useState('overview');

  const fetchAll = useCallback(async () => {
    try {
      const [overview, scheds] = await Promise.all([
        analyticsService.overview(),
        analyticsService.listSchedules(),
      ]);
      setAnalytics(overview.data);
      setSchedules(scheds.data);
    } catch (err) { console.error('Failed to load analytics', err); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  if (loading) return <div style={{ padding: '24px', color: '#888' }}>Loading analytics...</div>;

  return (
    <div style={{ padding: '24px' }}>
      <h1 style={{ fontSize: '28px', fontWeight: 700, margin: '0 0 8px' }}>Pipeline Analytics</h1>
      <p style={{ color: '#888', marginBottom: '24px' }}>Performance metrics, throughput, and scheduling</p>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '4px', marginBottom: '24px', borderBottom: '1px solid #333' }}>
        {['overview', 'stages', 'agents', 'throughput', 'scheduler'].map(t => (
          <button key={t} onClick={() => setTab(t)} style={tab === t ? tabActive : tabBtn}>
            {t.charAt(0).toUpperCase() + t.slice(1)}
          </button>
        ))}
      </div>

      {/* Overview Tab */}
      {tab === 'overview' && analytics && (
        <div>
          {/* Summary Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: '12px', marginBottom: '24px' }}>
            <StatCard label="Total Pipelines" value={analytics.summary.total_pipelines} />
            <StatCard label="Completed" value={analytics.summary.completed} color="#22C55E" />
            <StatCard label="Failed" value={analytics.summary.failed} color="#EF4444" />
            <StatCard label="Success Rate" value={`${analytics.summary.success_rate}%`} color="#4F46E5" />
            <StatCard label="Avg Duration" value={`${(analytics.summary.avg_duration_ms / 1000).toFixed(1)}s`} />
            <StatCard label="Total Retries" value={analytics.summary.total_retries} color="#FFA500" />
          </div>

          {/* Trends */}
          {analytics.trends && (
            <div style={{ background: '#1A1A1E', borderRadius: '10px', padding: '16px', marginBottom: '24px' }}>
              <h2 style={{ fontSize: '16px', marginBottom: '12px' }}>Trends (7-day comparison)</h2>
              <div style={{ display: 'flex', gap: '24px', flexWrap: 'wrap' }}>
                {Object.entries(analytics.trends.trends || {}).map(([key, val]) => (
                  <div key={key} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontSize: '13px', color: '#888' }}>{key.replace(/_/g, ' ')}:</span>
                    <span style={{ fontSize: '14px', color: trendColor(val) }}>{trendArrow(val)} {val}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Bottlenecks */}
          {analytics.bottlenecks && analytics.bottlenecks.length > 0 && (
            <div style={{ background: '#1A1A1E', borderRadius: '10px', padding: '16px' }}>
              <h2 style={{ fontSize: '16px', marginBottom: '12px', color: '#FF6B6B' }}>⚠ Stage Bottlenecks</h2>
              {analytics.bottlenecks.map((b, i) => (
                <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid #333' }}>
                  <span style={{ color: '#CCC' }}>{b.stage} <span style={{ color: '#666' }}>({b.agent})</span></span>
                  <span style={{ color: '#FF6B6B' }}>{(b.avg_duration_ms / 1000).toFixed(1)}s ({b.ratio}x avg)</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Stages Tab */}
      {tab === 'stages' && analytics && (
        <div style={{ background: '#1A1A1E', borderRadius: '10px', overflow: 'hidden' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid #333' }}>
                <th style={thStyle}>Stage</th>
                <th style={thStyle}>Agent</th>
                <th style={thStyle}>Runs</th>
                <th style={thStyle}>Passed</th>
                <th style={thStyle}>Failed</th>
                <th style={thStyle}>Success Rate</th>
                <th style={thStyle}>Avg Duration</th>
                <th style={thStyle}>Retries</th>
              </tr>
            </thead>
            <tbody>
              {(analytics.stages || []).map((s, i) => (
                <tr key={i} style={{ borderBottom: '1px solid #222' }}>
                  <td style={tdStyle}>{s.stage}</td>
                  <td style={{ ...tdStyle, color: '#4F46E5' }}>{s.agent}</td>
                  <td style={tdStyle}>{s.total_runs}</td>
                  <td style={{ ...tdStyle, color: '#22C55E' }}>{s.passed}</td>
                  <td style={{ ...tdStyle, color: s.failed > 0 ? '#EF4444' : '#666' }}>{s.failed}</td>
                  <td style={{ ...tdStyle, color: s.success_rate >= 80 ? '#22C55E' : s.success_rate >= 50 ? '#FFA500' : '#EF4444' }}>{s.success_rate}%</td>
                  <td style={tdStyle}>{(s.avg_duration_ms / 1000).toFixed(2)}s</td>
                  <td style={{ ...tdStyle, color: s.total_retries > 0 ? '#FFA500' : '#666' }}>{s.total_retries}</td>
                </tr>
              ))}
              {(!analytics.stages || analytics.stages.length === 0) && (
                <tr><td colSpan={8} style={{ ...tdStyle, textAlign: 'center', padding: '32px', color: '#666' }}>No stage data yet</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Agents Tab */}
      {tab === 'agents' && analytics && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '12px' }}>
          {(analytics.agents || []).map((a, i) => (
            <div key={i} style={{ background: '#1A1A1E', borderRadius: '10px', padding: '16px', border: '1px solid #333' }}>
              <h3 style={{ fontSize: '16px', color: '#4F46E5', marginBottom: '8px' }}>{a.agent}</h3>
              <div style={{ fontSize: '13px', color: '#888', marginBottom: '8px' }}>Stages: {a.stages.join(', ')}</div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px' }}>
                <span>Tasks: {a.total_tasks}</span>
                <span style={{ color: '#22C55E' }}>✓ {a.passed}</span>
                <span style={{ color: '#EF4444' }}>✗ {a.failed}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', marginTop: '8px' }}>
                <span style={{ color: '#888' }}>Success: <span style={{ color: a.success_rate >= 80 ? '#22C55E' : '#FFA500' }}>{a.success_rate}%</span></span>
                <span style={{ color: '#888' }}>Avg: {(a.avg_duration_ms / 1000).toFixed(2)}s</span>
              </div>
              {a.total_retries > 0 && <div style={{ fontSize: '12px', color: '#FFA500', marginTop: '4px' }}>↻ {a.total_retries} retries</div>}
            </div>
          ))}
          {(!analytics.agents || analytics.agents.length === 0) && (
            <div style={{ color: '#666', padding: '32px' }}>No agent data yet</div>
          )}
        </div>
      )}

      {/* Throughput Tab */}
      {tab === 'throughput' && analytics && (
        <div style={{ background: '#1A1A1E', borderRadius: '10px', padding: '16px' }}>
          <h2 style={{ fontSize: '16px', marginBottom: '12px' }}>Daily Throughput (Last 7 Days)</h2>
          <div style={{ display: 'flex', gap: '4px', alignItems: 'flex-end', height: '200px' }}>
            {(analytics.throughput?.data || []).map((d, i) => {
              const maxTotal = Math.max(...(analytics.throughput?.data || []).map(x => x.total), 1);
              const heightPct = (d.total / maxTotal) * 100;
              const completedPct = d.total > 0 ? (d.completed / d.total) * 100 : 0;
              return (
                <div key={i} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                  <div style={{ fontSize: '10px', color: '#888', marginBottom: '4px' }}>{d.total}</div>
                  <div style={{ width: '100%', maxWidth: '40px', background: '#0D0D0F', borderRadius: '4px 4px 0 0', height: `${heightPct}%`, display: 'flex', flexDirection: 'column-reverse' }}>
                    {d.completed > 0 && <div style={{ background: '#22C55E', height: `${completedPct}%`, borderRadius: '4px 4px 0 0' }} />}
                  </div>
                  <div style={{ fontSize: '10px', color: '#666', marginTop: '4px', transform: 'rotate(-45deg)' }}>{d.date.slice(5)}</div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Scheduler Tab */}
      {tab === 'scheduler' && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '16px' }}>
            <h2 style={{ fontSize: '20px' }}>Scheduled Pipelines ({schedules.length})</h2>
            <button onClick={() => setShowCreate(!showCreate)} style={btnPrimary}>{showCreate ? 'Cancel' : '+ New Schedule'}</button>
          </div>

          {showCreate && <CreateScheduleForm onCreate={async (s) => { await analyticsService.createSchedule(s); setShowCreate(false); fetchAll(); }} />}

          {schedules.length === 0 ? (
            <div style={{ padding: '32px', textAlign: 'center', color: '#666', background: '#1A1A1E', borderRadius: '10px' }}>
              No scheduled pipelines yet
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {schedules.map(s => (
                <div key={s.id} style={{ background: '#1A1A1E', borderRadius: '10px', padding: '16px', border: '1px solid #333' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <div>
                      <span style={{ fontWeight: 600 }}>{s.name}</span>
                      <span style={{ fontSize: '11px', padding: '2px 6px', borderRadius: '4px', marginLeft: '8px', background: s.enabled ? '#0D3D1A' : '#2A2A2E', color: s.enabled ? '#22C55E' : '#888' }}>
                        {s.enabled ? 'Active' : 'Disabled'}
                      </span>
                    </div>
                    <div style={{ display: 'flex', gap: '4px' }}>
                      <button onClick={async () => { s.enabled ? await analyticsService.disableSchedule(s.id) : await analyticsService.enableSchedule(s.id); fetchAll(); }} style={btnSmall}>
                        {s.enabled ? 'Disable' : 'Enable'}
                      </button>
                      <button onClick={async () => { await analyticsService.deleteSchedule(s.id); fetchAll(); }} style={{ ...btnSmall, background: '#5C1A1A' }}>Delete</button>
                    </div>
                  </div>
                  <div style={{ fontSize: '13px', color: '#888', marginTop: '4px' }}>
                    {s.schedule} at {s.time} · Template: {s.template_id} · Title: {s.title}
                  </div>
                  <div style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>
                    Next: {s.next_run ? new Date(s.next_run).toLocaleString() : '—'} · Runs: {s.run_count}{s.max_runs ? `/${s.max_runs}` : ''}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
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

function CreateScheduleForm({ onCreate }) {
  const [form, setForm] = useState({ name: '', template_id: 'bugfix', title: '', description: '', schedule: 'daily', time: '09:00', day_of_week: 0, day_of_month: 1 });
  return (
    <form onSubmit={e => { e.preventDefault(); onCreate(form); }} style={{ background: '#1A1A1E', padding: '20px', borderRadius: '10px', marginBottom: '24px' }}>
      <h2 style={{ fontSize: '18px', marginBottom: '12px' }}>New Schedule</h2>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
        <input placeholder="Name" value={form.name} onChange={e => setForm({...form, name: e.target.value})} style={inputStyle} required />
        <select value={form.template_id} onChange={e => setForm({...form, template_id: e.target.value})} style={inputStyle}>
          <option value="bugfix">Bug Fix</option><option value="new_feature">New Feature</option>
          <option value="refactor">Refactoring</option><option value="security_patch">Security Patch</option>
          <option value="infra_change">Infra Change</option><option value="hotfix">Hotfix</option>
        </select>
      </div>
      <input placeholder="Title" value={form.title} onChange={e => setForm({...form, title: e.target.value})} style={{ ...inputStyle, width: '100%', marginTop: '12px' }} required />
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '12px', marginTop: '12px' }}>
        <select value={form.schedule} onChange={e => setForm({...form, schedule: e.target.value})} style={inputStyle}>
          <option value="daily">Daily</option><option value="weekly">Weekly</option><option value="monthly">Monthly</option>
        </select>
        <input type="time" value={form.time} onChange={e => setForm({...form, time: e.target.value})} style={inputStyle} />
        {form.schedule === 'weekly' && (
          <select value={form.day_of_week} onChange={e => setForm({...form, day_of_week: parseInt(e.target.value)})} style={inputStyle}>
            <option value={0}>Monday</option><option value={1}>Tuesday</option><option value={2}>Wednesday</option>
            <option value={3}>Thursday</option><option value={4}>Friday</option><option value={5}>Saturday</option><option value={6}>Sunday</option>
          </select>
        )}
        {form.schedule === 'monthly' && (
          <input type="number" min={1} max={28} value={form.day_of_month} onChange={e => setForm({...form, day_of_month: parseInt(e.target.value)})} style={inputStyle} />
        )}
      </div>
      <button type="submit" style={{ marginTop: '12px', ...btnPrimary }}>Create Schedule</button>
    </form>
  );
}

function trendColor(val) { return val === 'up' ? '#22C55E' : val === 'down' ? '#EF4444' : '#888'; }
function trendArrow(val) { return val === 'up' ? '↑' : val === 'down' ? '↓' : '→'; }

const inputStyle = { padding: '8px 12px', background: '#0D0D0F', border: '1px solid #333', borderRadius: '6px', color: '#fff', fontSize: '14px' };
const btnPrimary = { padding: '8px 16px', background: '#4F46E5', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer' };
const btnSmall = { padding: '4px 12px', background: '#4F46E5', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '12px' };
const thStyle = { padding: '12px', textAlign: 'left', fontSize: '13px', color: '#888', fontWeight: 600 };
const tdStyle = { padding: '12px', fontSize: '13px', color: '#CCC' };
const tabBtn = { padding: '8px 16px', background: 'transparent', border: 'none', borderBottom: '2px solid transparent', color: '#888', cursor: 'pointer', fontSize: '14px' };
const tabActive = { ...tabBtn, color: '#4F46E5', borderBottom: '2px solid #4F46E5' };

export default PipelineAnalytics;
