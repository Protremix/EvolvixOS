import React from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Server, Cpu, Zap, Activity, CheckCircle, AlertCircle,
  HardDrive, Wifi
} from 'lucide-react';
import aiService from '../services/aiService';

const ExecutorStatus = () => {
  const { data: status, isLoading } = useQuery({
    queryKey: ['executor-status'],
    queryFn: aiService.getExecutorStatus,
    refetchInterval: 3000,
  });

  const { data: health } = useQuery({
    queryKey: ['ai-health'],
    queryFn: aiService.getHealth,
    refetchInterval: 5000,
    retry: false,
  });

  const { data: agents = [] } = useQuery({
    queryKey: ['ai-agents'],
    queryFn: aiService.getAgents,
    refetchInterval: 10000,
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div>
        <h1 style={{ fontSize: '1.75rem', fontWeight: '800', color: '#f0fdf4' }}>Executor Status</h1>
        <p style={{ color: '#8e9b8e', marginTop: '0.25rem', fontSize: '0.875rem' }}>
          Distributed executor health and worker monitoring
        </p>
      </div>

      {/* Main Status Cards */}
      <div className="grid-4">
        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <span style={{ fontSize: '0.875rem', color: '#8e9b8e' }}>Executor</span>
            <div style={{ width: 40, height: 40, borderRadius: 10, background: status?.is_running ? 'rgba(0,255,136,0.15)' : 'rgba(239,68,68,0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              {status?.is_running ? <CheckCircle size={20} color="#00ff88" /> : <AlertCircle size={20} color="#ef4444" />}
            </div>
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: '800', color: status?.is_running ? '#00ff88' : '#ef4444' }}>
            {isLoading ? '...' : status?.is_running ? 'Running' : 'Stopped'}
          </div>
        </div>

        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <span style={{ fontSize: '0.875rem', color: '#8e9b8e' }}>Active Tasks</span>
            <div style={{ width: 40, height: 40, borderRadius: 10, background: 'rgba(59,130,246,0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Activity size={20} color="#3b82f6" />
            </div>
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: '800', color: '#f0fdf4' }}>
            {status?.active_tasks || 0}
          </div>
        </div>

        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <span style={{ fontSize: '0.875rem', color: '#8e9b8e' }}>Workers</span>
            <div style={{ width: 40, height: 40, borderRadius: 10, background: 'rgba(168,85,247,0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Server size={20} color="#a855f7" />
            </div>
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: '800', color: '#f0fdf4' }}>
            {status?.worker_count || 3}
          </div>
        </div>

        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <span style={{ fontSize: '0.875rem', color: '#8e9b8e' }}>Completed</span>
            <div style={{ width: 40, height: 40, borderRadius: 10, background: 'rgba(0,255,136,0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <CheckCircle size={20} color="#00ff88" />
            </div>
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: '800', color: '#f0fdf4' }}>
            {status?.total_completed || 0}
          </div>
        </div>
      </div>

      {/* Health Check */}
      <div className="card">
        <h2 style={{ fontSize: '1.1rem', fontWeight: '700', color: '#f0fdf4', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <HardDrive size={20} color="#00ff88" />
          System Health
        </h2>
        {health ? (
          <div className="grid-3">
            <div>
              <div style={{ fontSize: '0.75rem', color: '#8e9b8e' }}>Status</div>
              <div style={{ fontSize: '1rem', fontWeight: '700', color: '#00ff88' }}>{health.status || 'OK'}</div>
            </div>
            <div>
              <div style={{ fontSize: '0.75rem', color: '#8e9b8e' }}>LLM Available</div>
              <div style={{ fontSize: '1rem', fontWeight: '700', color: health.llm_available ? '#00ff88' : '#ef4444' }}>
                {health.llm_available ? 'Yes' : 'No'}
              </div>
            </div>
            <div>
              <div style={{ fontSize: '0.75rem', color: '#8e9b8e' }}>Active Agents</div>
              <div style={{ fontSize: '1rem', fontWeight: '700', color: '#f0fdf4' }}>{agents.length}</div>
            </div>
          </div>
        ) : (
          <p style={{ color: '#526352', fontSize: '0.875rem' }}>Health endpoint not available.</p>
        )}
      </div>

      {/* Agent Swarm Overview */}
      <div className="card">
        <h2 style={{ fontSize: '1.1rem', fontWeight: '700', color: '#f0fdf4', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Wifi size={20} color="#3b82f6" />
          Agent Swarm ({agents.length})
        </h2>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid #1f2e1f' }}>
                <th style={{ textAlign: 'left', padding: '0.625rem', fontSize: '0.75rem', color: '#8e9b8e', fontWeight: '600' }}>Agent</th>
                <th style={{ textAlign: 'left', padding: '0.625rem', fontSize: '0.75rem', color: '#8e9b8e', fontWeight: '600' }}>Status</th>
                <th style={{ textAlign: 'left', padding: '0.625rem', fontSize: '0.75rem', color: '#8e9b8e', fontWeight: '600' }}>Model</th>
                <th style={{ textAlign: 'left', padding: '0.625rem', fontSize: '0.75rem', color: '#8e9b8e', fontWeight: '600' }}>Tasks</th>
              </tr>
            </thead>
            <tbody>
              {agents.map((a, i) => (
                <tr key={i} style={{ borderBottom: '1px solid #0e140e' }}>
                  <td style={{ padding: '0.625rem', fontSize: '0.8125rem', color: '#f0fdf4', fontWeight: '600' }}>
                    {a.display_name || a.name}
                  </td>
                  <td style={{ padding: '0.625rem' }}>
                    <span style={{
                      display: 'inline-flex', alignItems: 'center', gap: '0.25rem',
                      padding: '0.125rem 0.5rem', borderRadius: '9999px', fontSize: '0.6875rem', fontWeight: '600',
                      backgroundColor: a.status === 'active' ? 'rgba(0,255,136,0.12)' : 'rgba(142,155,142,0.12)',
                      color: a.status === 'active' ? '#00ff88' : '#8e9b8e',
                    }}>
                      <span style={{ width: 6, height: 6, borderRadius: '50%', backgroundColor: 'currentColor' }} />
                      {a.status || 'idle'}
                    </span>
                  </td>
                  <td style={{ padding: '0.625rem', fontSize: '0.8125rem', color: '#8e9b8e' }}>{a.model || 'GPT-4o'}</td>
                  <td style={{ padding: '0.625rem', fontSize: '0.8125rem', color: '#f0fdf4', fontWeight: '600' }}>
                    {a.tasks_completed || 0}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default ExecutorStatus;
