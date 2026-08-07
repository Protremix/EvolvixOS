import React, { useState, useEffect, useCallback } from 'react';
import agentLearningService from '../services/agentLearningService';

function AgentLearning() {
  const [tab, setTab] = useState('performance');
  const [summary, setSummary] = useState(null);
  const [performance, setPerformance] = useState([]);
  const [insights, setInsights] = useState([]);
  const [promptOpts, setPromptOpts] = useState([]);

  const fetchAll = useCallback(async () => {
    try {
      const [sResp, pResp, iResp, oResp] = await Promise.all([
        agentLearningService.summary(),
        agentLearningService.performance(),
        agentLearningService.insights(null, null, 30),
        agentLearningService.promptOpts(),
      ]);
      setSummary(sResp.data);
      setPerformance(pResp.data);
      setInsights(iResp.data);
      setPromptOpts(oResp.data);
    } catch (err) { console.error(err); }
  }, []);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  const handleAnalyze = async () => {
    try { await agentLearningService.analyze(); fetchAll(); }
    catch (err) { console.error(err); }
  };

  return (
    <div style={{ padding: '24px' }}>
      <h1 style={{ fontSize: '28px', fontWeight: 700, marginBottom: '4px' }}>🧠 Agent Learning</h1>
      <p style={{ color: '#888', marginBottom: '24px' }}>Self-improvement loop — agents learn from past results</p>

      {summary && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(120px, 1fr))', gap: '8px', marginBottom: '20px' }}>
          <Stat label="Executions" value={summary.total_executions} />
          <Stat label="Insights" value={summary.total_insights} color="#4F46E5" />
          <Stat label="Actionable" value={summary.actionable_insights} color="#FFA500" />
          <Stat label="Prompt Opts" value={summary.total_prompt_opts} color="#22C55E" />
          <Stat label="Agents" value={summary.agents_tracked} />
          <Stat label="Task Types" value={summary.task_types_tracked} />
        </div>
      )}

      <div style={{ display: 'flex', gap: '4px', marginBottom: '16px' }}>
        {['performance', 'insights', 'prompts'].map(t => (
          <button key={t} onClick={() => setTab(t)} style={{
            padding: '6px 16px', border: '1px solid #333', borderRadius: '6px 6px 0 0',
            background: tab === t ? '#4F46E5' : '#1A1A1E', color: tab === t ? '#fff' : '#888',
            cursor: 'pointer', fontSize: '13px', textTransform: 'capitalize',
          }}>{t}</button>
        ))}
        <button onClick={handleAnalyze} style={{ marginLeft: 'auto', padding: '6px 16px', background: '#22C55E', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '12px' }}>⚡ Analyze</button>
      </div>

      {/* Performance Tab */}
      {tab === 'performance' && (
        <div style={{ display: 'grid', gap: '8px' }}>
          {performance.length === 0 && <div style={{ color: '#888' }}>No execution data yet. Record agent executions to see performance metrics.</div>}
          {performance.map(p => (
            <div key={p.agent_name} style={{ ...panel }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                <span style={{ fontSize: '14px', fontWeight: 600 }}>{p.agent_name}</span>
                <Badge color={p.success_rate >= 90 ? '#22C55E' : p.success_rate >= 70 ? '#FFA500' : '#EF4444'}>{p.success_rate}% success</Badge>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(90px, 1fr))', gap: '4px' }}>
                <Mini label="Total" value={p.total_executions} />
                <Mini label="Avg Score" value={p.avg_score?.toFixed(1) || 0} color={p.avg_score >= 8 ? '#22C55E' : '#FFA500'} />
                <Mini label="Min" value={p.min_score?.toFixed(1) || 0} />
                <Mini label="Max" value={p.max_score?.toFixed(1) || 0} />
                <Mini label="GO Rate" value={`${p.go_rate}%`} color={p.go_rate > 80 ? '#22C55E' : '#888'} />
                <Mini label="Avg Tokens" value={p.avg_tokens || 0} />
                <Mini label="Latency" value={`${(p.avg_latency_ms || 0).toFixed(0)}ms`} />
              </div>
              {p.recent_trend && p.recent_trend.length > 1 && (
                <div style={{ marginTop: '8px' }}>
                  <div style={{ fontSize: '10px', color: '#666', marginBottom: '4px' }}>Recent trend:</div>
                  <div style={{ display: 'flex', gap: '2px', alignItems: 'flex-end', height: '30px' }}>
                    {p.recent_trend.map((s, i) => (
                      <div key={i} style={{ width: '8px', height: `${(s / 10) * 100}%`, background: s >= 8 ? '#22C55E' : s >= 6 ? '#FFA500' : '#EF4444', borderRadius: '2px 2px 0 0' }} title={s.toFixed(1)} />
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Insights Tab */}
      {tab === 'insights' && (
        <div style={{ display: 'grid', gap: '6px' }}>
          {insights.length === 0 && <div style={{ color: '#888' }}>No insights yet. Click Analyze to generate insights from execution history.</div>}
          {insights.map(i => (
            <div key={i.id} style={{ ...panel, padding: '10px 14px' }}>
              <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                <Badge color={i.insight_type === 'performance_trend' ? '#22C55E' : i.insight_type === 'score_regression' ? '#EF4444' : i.insight_type === 'failure_pattern' ? '#EF4444' : i.insight_type === 'success_pattern' ? '#4F46E5' : '#FFA500'}>{i.insight_type.replace(/_/g, ' ')}</Badge>
                <Badge color="#666">{i.agent_name}</Badge>
                {i.actionable && <Badge color="#FFA500">actionable</Badge>}
                <span style={{ fontSize: '12px', color: '#CCC', flex: 1 }}>{i.description}</span>
              </div>
              {i.recommendation && (
                <div style={{ fontSize: '12px', color: '#4F46E5', marginTop: '4px', paddingLeft: '12px' }}>→ {i.recommendation}</div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Prompts Tab */}
      {tab === 'prompts' && (
        <div style={{ display: 'grid', gap: '6px' }}>
          {promptOpts.length === 0 && <div style={{ color: '#888' }}>No prompt optimization suggestions yet.</div>}
          {promptOpts.map(o => (
            <div key={o.id} style={{ ...panel, padding: '10px 14px' }}>
              <div style={{ display: 'flex', gap: '8px', marginBottom: '4px' }}>
                <Badge color="#4F46E5">{o.agent_name}</Badge>
                <Badge color={o.confidence > 0.7 ? '#22C55E' : '#FFA500'}>{(o.confidence * 100).toFixed(0)}% confidence</Badge>
                {o.applied && <Badge color="#22C55E">applied</Badge>}
              </div>
              <div style={{ fontSize: '12px', color: '#EF4444', marginBottom: '2px' }}>⚠ {o.current_issue}</div>
              <div style={{ fontSize: '12px', color: '#22C55E' }}>✓ {o.suggested_improvement}</div>
              <div style={{ fontSize: '11px', color: '#666', marginTop: '4px' }}>Evidence: {o.evidence}</div>
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
function Mini({ label, value, color }) {
  return (
    <div style={{ background: '#0D0D0F', borderRadius: '4px', padding: '4px 8px' }}>
      <div style={{ fontSize: '9px', color: '#666' }}>{label}</div>
      <div style={{ fontSize: '13px', fontWeight: 600, color: color || '#CCC' }}>{value}</div>
    </div>
  );
}
function Badge({ color, children }) {
  return <span style={{ fontSize: '10px', padding: '2px 6px', borderRadius: '4px', background: color + '22', color, fontWeight: 600 }}>{children}</span>;
}
const panel = { background: '#1A1A1E', borderRadius: '10px', border: '1px solid #333', padding: '12px 16px' };

export default AgentLearning;
