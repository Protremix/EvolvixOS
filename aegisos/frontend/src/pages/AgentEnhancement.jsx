import React, { useState, useEffect, useCallback } from 'react';
import agentEnhancementService from '../services/agentEnhancementService';

function AgentEnhancement() {
  const [scenarios, setScenarios] = useState([]);
  const [stats, setStats] = useState(null);
  const [overview, setOverview] = useState(null);
  const [simResult, setSimResult] = useState(null);
  const [running, setRunning] = useState(null);
  const [tab, setTab] = useState('scenarios');

  const fetchAll = useCallback(async () => {
    try {
      const [sResp, statsResp, ovResp] = await Promise.all([
        agentEnhancementService.listScenarios(),
        agentEnhancementService.simStats(),
        agentEnhancementService.overview(),
      ]);
      setScenarios(sResp.data);
      setStats(statsResp.data);
      setOverview(ovResp.data);
    } catch (err) { console.error(err); }
  }, []);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  const handleRun = async (id) => {
    setRunning(id);
    try {
      const resp = await agentEnhancementService.runSimulation(id);
      setSimResult(resp.data);
    } catch (err) { console.error(err); }
    finally { setRunning(null); }
  };

  return (
    <div style={{ padding: '24px' }}>
      <h1 style={{ fontSize: '28px', fontWeight: 700, marginBottom: '4px' }}>🤖 Agent Enhancement</h1>
      <p style={{ color: '#888', marginBottom: '24px' }}>AI agent simulation, Verdis context injection, and activity tracking</p>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '4px', marginBottom: '16px' }}>
        {['scenarios', 'simulation', 'context', 'activities'].map(t => (
          <button key={t} onClick={() => setTab(t)} style={{
            padding: '6px 16px', border: '1px solid #333', borderRadius: '6px 6px 0 0',
            background: tab === t ? '#4F46E5' : '#1A1A1E', color: tab === t ? '#fff' : '#888',
            cursor: 'pointer', fontSize: '13px', textTransform: 'capitalize',
          }}>{t}</button>
        ))}
      </div>

      {/* Scenarios Tab */}
      {tab === 'scenarios' && (
        <div>
          {stats && (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(120px, 1fr))', gap: '8px', marginBottom: '16px' }}>
              <Stat label="Scenarios" value={stats.total_scenarios} />
              <Stat label="Builtin" value={stats.builtin_scenarios} />
              <Stat label="Custom" value={stats.custom_scenarios} />
              <Stat label="Executions" value={stats.total_executions} />
              <Stat label="Agents" value={stats.agents_covered?.length || 0} color="#4F46E5" />
            </div>
          )}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {scenarios.map(s => (
              <div key={s.id} style={{ ...panel, padding: '12px 16px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <div style={{ fontSize: '14px', fontWeight: 600 }}>{s.name}</div>
                    <div style={{ fontSize: '11px', color: '#888' }}>{s.description}</div>
                    <div style={{ display: 'flex', gap: '4px', marginTop: '4px' }}>
                      <Badge color="#4F46E5">{s.agent_name}</Badge>
                      <Badge color="#666">{s.task_type}</Badge>
                      {s.tags?.map(t => <Badge key={t} color="#2A2A2E">{t}</Badge>)}
                    </div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: '16px', fontWeight: 700, color: s.mock_score >= 8 ? '#22C55E' : s.mock_score >= 7 ? '#FFA500' : '#EF4444' }}>{s.mock_score}/10</div>
                    <Badge color={s.mock_verdict === 'GO' ? '#22C55E' : '#EF4444'}>{s.mock_verdict}</Badge>
                    <button onClick={() => handleRun(s.id)} disabled={running === s.id} style={{ ...btn, marginTop: '4px' }}>
                      {running === s.id ? 'Running...' : '▶ Run'}
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Simulation Result Tab */}
      {tab === 'simulation' && simResult && (
        <div>
          <div style={{ ...panel, marginBottom: '12px' }}>
            <h3 style={{ margin: '0 0 8px' }}>{simResult.scenario_name}</h3>
            <div style={{ display: 'flex', gap: '8px', marginBottom: '8px' }}>
              <Badge color="#4F46E5">{simResult.agent_name}</Badge>
              <Badge color={simResult.verdict === 'GO' ? '#22C55E' : '#EF4444'}>{simResult.verdict}</Badge>
              <span style={{ fontSize: '20px', fontWeight: 700, color: '#4F46E5' }}>{simResult.score}/10</span>
            </div>
            <pre style={{ fontSize: '13px', color: '#CCC', whiteSpace: 'pre-wrap', margin: '8px 0' }}>{simResult.output?.summary}</pre>
            {simResult.findings?.length > 0 && (
              <div style={{ marginTop: '12px' }}>
                <div style={{ fontSize: '12px', color: '#888', marginBottom: '4px' }}>Findings ({simResult.findings.length}):</div>
                {simResult.findings.map((f, i) => (
                  <div key={i} style={{ display: 'flex', gap: '6px', padding: '4px 0' }}>
                    <Badge color={f.severity === 'High' ? '#EF4444' : f.severity === 'Medium' ? '#FFA500' : '#888'}>{f.severity}</Badge>
                    <span style={{ fontSize: '12px', color: '#CCC' }}>{f.description}</span>
                  </div>
                ))}
              </div>
            )}
            {simResult.recommendations?.length > 0 && (
              <div style={{ marginTop: '12px' }}>
                <div style={{ fontSize: '12px', color: '#888', marginBottom: '4px' }}>Recommendations ({simResult.recommendations.length}):</div>
                {simResult.recommendations.map((r, i) => (
                  <div key={i} style={{ fontSize: '12px', color: '#4F46E5', padding: '2px 12px' }}>• {r}</div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
      {tab === 'simulation' && !simResult && <div style={{ color: '#888' }}>Run a scenario to see results.</div>}

      {/* Verdis Context Tab */}
      {tab === 'context' && overview && (
        <div>
          <div style={{ ...panel, marginBottom: '12px' }}>
            <h3 style={{ margin: '0 0 8px' }}>Verdis Agent Context</h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))', gap: '8px' }}>
              <Stat label="Chain" value={overview.context?.chain_name} />
              <Stat label="Consensus" value={overview.context?.consensus?.substring(0, 15)} />
              <Stat label="Validators" value={`${overview.context?.validator_count}/${overview.context?.target_validators}`} />
              <Stat label="Spec" value={`v${overview.context?.spec_version}`} />
              <Stat label="Pallets" value={overview.context?.pallets?.length} color="#4F46E5" />
              <Stat label="Nodes" value={overview.context?.node_count} />
            </div>
            <div style={{ marginTop: '12px' }}>
              <div style={{ fontSize: '12px', color: '#888', marginBottom: '4px' }}>Pallets:</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                {overview.context?.pallets?.map(p => <Badge key={p} color="#4F46E5">{p}</Badge>)}
              </div>
            </div>
          </div>
          <div style={{ ...panel }}>
            <h3 style={{ margin: '0 0 8px' }}>Verdis-Specific Task Types ({Object.keys(overview.verdis_task_types || {}).length})</h3>
            {Object.entries(overview.verdis_task_types || {}).map(([k, v]) => (
              <div key={k} style={{ display: 'flex', gap: '8px', padding: '4px 0' }}>
                <Badge color="#4F46E5">{k}</Badge>
                <span style={{ fontSize: '12px', color: '#888' }}>{v}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Activities Tab */}
      {tab === 'activities' && overview && (
        <div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(120px, 1fr))', gap: '8px', marginBottom: '16px' }}>
            <Stat label="Total Activities" value={overview.total_activities} />
            <Stat label="Active Agents" value={overview.total_agents} color="#4F46E5" />
          </div>
          {overview.agent_stats?.map(a => (
            <div key={a.agent_name} style={{ ...panel, marginBottom: '8px', padding: '12px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ fontSize: '14px', fontWeight: 600 }}>{a.agent_name}</span>
                <span style={{ fontSize: '12px', color: '#888' }}>{a.total_tasks} tasks</span>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(100px, 1fr))', gap: '4px', marginTop: '8px' }}>
                <MiniStat label="Completed" value={a.completed} color="#22C55E" />
                <MiniStat label="Failed" value={a.failed} color="#EF4444" />
                <MiniStat label="GO" value={a.go_verdicts} color="#22C55E" />
                <MiniStat label="NO-GO" value={a.nogo_verdicts} color="#EF4444" />
                <MiniStat label="Avg Score" value={a.avg_score?.toFixed(1) || 0} />
                <MiniStat label="Tokens" value={a.total_tokens} />
              </div>
            </div>
          ))}
          {overview.agent_stats?.length === 0 && <div style={{ color: '#888' }}>No agent activities recorded yet.</div>}
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

function MiniStat({ label, value, color }) {
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

const panel = { background: '#1A1A1E', borderRadius: '10px', border: '1px solid #333' };
const btn = { padding: '4px 12px', background: '#4F46E5', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '12px' };

export default AgentEnhancement;
