import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  Bot, Cpu, Shield, Bug, Calendar, FileText, Brain, Eye,
  Activity, CheckCircle, Clock, AlertCircle, Plus, Zap
} from 'lucide-react';
import aiService from '../services/aiService';

const AGENT_ICONS = {
  cto: Bot,
  architect: Cpu,
  security: Shield,
  qa: Bug,
  planner: Calendar,
  reviewer: Eye,
  documentation: FileText,
  memory: Brain,
};

const AGENT_COLORS = {
  cto: '#00ff88',
  architect: '#3b82f6',
  security: '#ef4444',
  qa: '#f59e0b',
  planner: '#a855f7',
  reviewer: '#06b6d4',
  documentation: '#ec4899',
  memory: '#10b981',
};

const STATUS_BADGE = {
  active: { bg: 'rgba(0,255,136,0.12)', border: 'rgba(0,255,136,0.25)', color: '#00ff88', icon: CheckCircle },
  idle: { bg: 'rgba(142,155,142,0.12)', border: 'rgba(142,155,142,0.25)', color: '#8e9b8e', icon: Clock },
  error: { bg: 'rgba(239,68,68,0.12)', border: 'rgba(239,68,68,0.25)', color: '#ef4444', icon: AlertCircle },
};

const Agents = () => {
  const [filter, setFilter] = useState('all');

  const { data: agents = [], isLoading } = useQuery({
    queryKey: ['ai-agents'],
    queryFn: aiService.getAgents,
    refetchInterval: 5000,
  });

  const { data: executorStatus } = useQuery({
    queryKey: ['executor-status'],
    queryFn: aiService.getExecutorStatus,
    refetchInterval: 5000,
  });

  const filteredAgents = agents.filter(a => {
    if (filter === 'all') return true;
    if (filter === 'active') return a.status === 'active';
    if (filter === 'idle') return a.status === 'idle';
    return true;
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: '800', color: '#f0fdf4' }}>AI Agents</h1>
          <p style={{ color: '#8e9b8e', marginTop: '0.25rem', fontSize: '0.875rem' }}>
            Real-time monitoring of all {agents.length || 8} AI agents in the EvolvixOS swarm
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          {['all', 'active', 'idle'].map(f => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              style={{
                padding: '0.5rem 1rem',
                borderRadius: '8px',
                border: filter === f ? '1px solid #00ff88' : '1px solid #1f2e1f',
                backgroundColor: filter === f ? 'rgba(0,255,136,0.1)' : 'transparent',
                color: filter === f ? '#00ff88' : '#8e9b8e',
                cursor: 'pointer',
                fontSize: '0.8125rem',
                fontWeight: '600',
                textTransform: 'capitalize',
              }}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      {/* Executor Status Bar */}
      {executorStatus && (
        <div style={{
          backgroundColor: '#121812',
          border: '1px solid #1f2e1f',
          borderRadius: '12px',
          padding: '1.25rem',
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
          gap: '1rem',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <div style={{ width: 40, height: 40, borderRadius: 10, background: 'rgba(0,255,136,0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Zap size={20} color="#00ff88" />
            </div>
            <div>
              <div style={{ fontSize: '0.75rem', color: '#8e9b8e' }}>Executor</div>
              <div style={{ fontSize: '1.1rem', fontWeight: '700', color: executorStatus.is_running ? '#00ff88' : '#ef4444' }}>
                {executorStatus.is_running ? 'Running' : 'Stopped'}
              </div>
            </div>
          </div>
          <div>
            <div style={{ fontSize: '0.75rem', color: '#8e9b8e' }}>Active Tasks</div>
            <div style={{ fontSize: '1.1rem', fontWeight: '700', color: '#f0fdf4' }}>{executorStatus.active_tasks || 0}</div>
          </div>
          <div>
            <div style={{ fontSize: '0.75rem', color: '#8e9b8e' }}>Workers</div>
            <div style={{ fontSize: '1.1rem', fontWeight: '700', color: '#f0fdf4' }}>{executorStatus.worker_count || 3}</div>
          </div>
          <div>
            <div style={{ fontSize: '0.75rem', color: '#8e9b8e' }}>Completed</div>
            <div style={{ fontSize: '1.1rem', fontWeight: '700', color: '#f0fdf4' }}>{executorStatus.total_completed || 0}</div>
          </div>
        </div>
      )}

      {/* Agent Cards Grid */}
      <div className="grid-4">
        {isLoading ? (
          <div style={{ color: '#8e9b8e', padding: '2rem' }}>Loading agents...</div>
        ) : (
          filteredAgents.map((agent, idx) => {
            const iconName = (agent.name || '').toLowerCase().replace('_agent', '').replace(' ', '');
            const Icon = AGENT_ICONS[iconName] || Bot;
            const color = AGENT_COLORS[iconName] || '#00ff88';
            const status = STATUS_BADGE[agent.status] || STATUS_BADGE.idle;
            const StatusIcon = status.icon;

            return (
              <Link
                key={idx}
                to={`/agents/${encodeURIComponent(agent.name || agent.id)}`}
                style={{ textDecoration: 'none' }}
              >
                <div
                  className="card"
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '0.75rem',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease',
                  }}
                  onMouseEnter={e => { e.currentTarget.style.borderColor = color + '60'; }}
                  onMouseLeave={e => { e.currentTarget.style.borderColor = '#1f2e1f'; }}
                >
                  {/* Agent Header */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div style={{
                      width: 48, height: 48, borderRadius: 12,
                      backgroundColor: `${color}15`,
                      border: `1px solid ${color}30`,
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                    }}>
                      <Icon size={24} color={color} />
                    </div>
                    <div style={{
                      display: 'inline-flex', alignItems: 'center', gap: '0.375rem',
                      padding: '0.25rem 0.625rem', borderRadius: '9999px',
                      backgroundColor: status.bg, border: `1px solid ${status.border}`,
                      fontSize: '0.6875rem', fontWeight: '600', color: status.color,
                    }}>
                      <StatusIcon size={11} />
                      <span style={{ textTransform: 'capitalize' }}>{agent.status || 'idle'}</span>
                    </div>
                  </div>

                  {/* Agent Name & Description */}
                  <div>
                    <div style={{ fontSize: '1rem', fontWeight: '700', color: '#f0fdf4' }}>
                      {agent.display_name || agent.name || 'Unknown Agent'}
                    </div>
                    <div style={{ fontSize: '0.75rem', color: '#8e9b8e', marginTop: '0.25rem' }}>
                      {agent.description || 'No description available'}
                    </div>
                  </div>

                  {/* Agent Stats */}
                  <div style={{ display: 'flex', gap: '1rem', marginTop: 'auto', paddingTop: '0.5rem', borderTop: '1px solid #1f2e1f' }}>
                    <div>
                      <div style={{ fontSize: '0.6875rem', color: '#526352' }}>Tasks</div>
                      <div style={{ fontSize: '0.9375rem', fontWeight: '700', color: '#f0fdf4' }}>
                        {agent.tasks_completed || agent.total_tasks || 0}
                      </div>
                    </div>
                    <div>
                      <div style={{ fontSize: '0.6875rem', color: '#526352' }}>Types</div>
                      <div style={{ fontSize: '0.9375rem', fontWeight: '700', color: '#f0fdf4' }}>
                        {agent.supported_types?.length || agent.task_types?.length || 0}
                      </div>
                    </div>
                    <div>
                      <div style={{ fontSize: '0.6875rem', color: '#526352' }}>Model</div>
                      <div style={{ fontSize: '0.9375rem', fontWeight: '700', color: '#f0fdf4' }}>
                        {agent.model || 'GPT-4o'}
                      </div>
                    </div>
                  </div>
                </div>
              </Link>
            );
          })
        )}
      </div>

      {/* Fallback if no agents returned from API */}
      {!isLoading && agents.length === 0 && (
        <div style={{
          backgroundColor: '#121812', border: '1px solid #1f2e1f', borderRadius: '12px',
          padding: '2rem', textAlign: 'center',
        }}>
          <Bot size={48} color="#1f2e1f" style={{ margin: '0 auto 1rem' }} />
          <p style={{ color: '#8e9b8e', marginBottom: '1rem' }}>
            No agents returned from the API. The AI core may not be running.
          </p>
          <p style={{ color: '#526352', fontSize: '0.8125rem' }}>
            Make sure the backend is running and the /api/v1/ai/agents endpoint is accessible.
          </p>
        </div>
      )}
    </div>
  );
};

export default Agents;
