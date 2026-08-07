import React, { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import {
  GitBranch, Play, Plus, Clock, CheckCircle, Loader,
  AlertCircle, Zap, ArrowRight
} from 'lucide-react';
import aiService from '../services/aiService';

const STATUS_CONFIG = {
  pending: { icon: Clock, color: '#f59e0b', bg: 'rgba(245,158,11,0.12)' },
  running: { icon: Loader, color: '#3b82f6', bg: 'rgba(59,130,246,0.12)' },
  completed: { icon: CheckCircle, color: '#00ff88', bg: 'rgba(0,255,136,0.12)' },
  failed: { icon: AlertCircle, color: '#ef4444', bg: 'rgba(239,68,68,0.12)' },
};

const Pipelines = () => {
  const [showForm, setShowForm] = useState(false);
  const [taskType, setTaskType] = useState('');
  const [description, setDescription] = useState('');
  const [agentName, setAgentName] = useState('');

  const { data: agents = [] } = useQuery({
    queryKey: ['ai-agents'],
    queryFn: aiService.getAgents,
  });

  const { data: executorStatus } = useQuery({
    queryKey: ['executor-status'],
    queryFn: aiService.getExecutorStatus,
    refetchInterval: 5000,
  });

  const dispatchMutation = useMutation({
    mutationFn: (data) => aiService.dispatchTask(data),
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    dispatchMutation.mutate({
      task_type: taskType,
      description,
      agent_name: agentName || undefined,
    }, {
      onSuccess: () => {
        setTaskType('');
        setDescription('');
        setAgentName('');
        setShowForm(false);
      },
    });
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: '800', color: '#f0fdf4' }}>Task Pipelines</h1>
          <p style={{ color: '#8e9b8e', marginTop: '0.25rem', fontSize: '0.875rem' }}>
            Dispatch and monitor AI tasks across the agent swarm
          </p>
        </div>
        <button onClick={() => setShowForm(!showForm)} className="btn btn-primary" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem' }}>
          <Plus size={18} />
          <span>New Task</span>
        </button>
      </div>

      {/* Dispatch Form */}
      {showForm && (
        <form onSubmit={handleSubmit} className="card" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <h2 style={{ fontSize: '1.1rem', fontWeight: '700', color: '#f0fdf4' }}>Dispatch New Task</h2>
          <div>
            <label style={{ display: 'block', fontSize: '0.8125rem', color: '#8e9b8e', marginBottom: '0.375rem' }}>Task Type</label>
            <input
              type="text" value={taskType} onChange={e => setTaskType(e.target.value)} required
              placeholder="e.g. architecture_review, code_review, sprint_planning"
              style={{ width: '100%', padding: '0.625rem 0.875rem', backgroundColor: '#0e140e', border: '1px solid #1f2e1f', borderRadius: '8px', color: '#f0fdf4', fontSize: '0.875rem', outline: 'none' }}
            />
          </div>
          <div>
            <label style={{ display: 'block', fontSize: '0.8125rem', color: '#8e9b8e', marginBottom: '0.375rem' }}>Description</label>
            <textarea
              value={description} onChange={e => setDescription(e.target.value)} rows={3}
              placeholder="Describe the task..."
              style={{ width: '100%', padding: '0.625rem 0.875rem', backgroundColor: '#0e140e', border: '1px solid #1f2e1f', borderRadius: '8px', color: '#f0fdf4', fontSize: '0.875rem', outline: 'none', resize: 'vertical' }}
            />
          </div>
          <div>
            <label style={{ display: 'block', fontSize: '0.8125rem', color: '#8e9b8e', marginBottom: '0.375rem' }}>Agent (optional)</label>
            <select
              value={agentName} onChange={e => setAgentName(e.target.value)}
              style={{ width: '100%', padding: '0.625rem 0.875rem', backgroundColor: '#0e140e', border: '1px solid #1f2e1f', borderRadius: '8px', color: '#f0fdf4', fontSize: '0.875rem', outline: 'none' }}
            >
              <option value="">Auto-assign</option>
              {agents.map((a, i) => (
                <option key={i} value={a.name}>{a.display_name || a.name}</option>
              ))}
            </select>
          </div>
          {dispatchMutation.isError && (
            <div style={{ color: '#ef4444', fontSize: '0.8125rem' }}>
              Error: {dispatchMutation.error?.message}
            </div>
          )}
          {dispatchMutation.isSuccess && (
            <div style={{ color: '#00ff88', fontSize: '0.8125rem' }}>
              Task dispatched successfully! Task ID: {dispatchMutation.data?.task_id}
            </div>
          )}
          <button type="submit" disabled={dispatchMutation.isPending} className="btn btn-primary" style={{ alignSelf: 'flex-start' }}>
            {dispatchMutation.isPending ? 'Dispatching...' : 'Dispatch Task'}
          </button>
        </form>
      )}

      {/* Executor Status */}
      {executorStatus && (
        <div className="card">
          <h2 style={{ fontSize: '1.1rem', fontWeight: '700', color: '#f0fdf4', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Zap size={20} color="#00ff88" />
            Executor Status
          </h2>
          <div className="grid-4">
            <div>
              <div style={{ fontSize: '0.75rem', color: '#8e9b8e' }}>Status</div>
              <div style={{ fontSize: '1.1rem', fontWeight: '700', color: executorStatus.is_running ? '#00ff88' : '#ef4444' }}>
                {executorStatus.is_running ? 'Running' : 'Stopped'}
              </div>
            </div>
            <div>
              <div style={{ fontSize: '0.75rem', color: '#8e9b8e' }}>Active Tasks</div>
              <div style={{ fontSize: '1.1rem', fontWeight: '700', color: '#f0fdf4' }}>{executorStatus.active_tasks || 0}</div>
            </div>
            <div>
              <div style={{ fontSize: '0.75rem', color: '#8e9b8e' }}>Queue Size</div>
              <div style={{ fontSize: '1.1rem', fontWeight: '700', color: '#f0fdf4' }}>{executorStatus.queue_size || 0}</div>
            </div>
            <div>
              <div style={{ fontSize: '0.75rem', color: '#8e9b8e' }}>Workers</div>
              <div style={{ fontSize: '1.1rem', fontWeight: '700', color: '#f0fdf4' }}>{executorStatus.worker_count || 3}</div>
            </div>
          </div>
        </div>
      )}

      {/* Pipeline Flow Visualization */}
      <div className="card">
        <h2 style={{ fontSize: '1.1rem', fontWeight: '700', color: '#f0fdf4', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <GitBranch size={20} color="#3b82f6" />
          Pipeline Flow
        </h2>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
          {['Dispatch', 'Queue', 'Agent', 'Execute', 'Result'].map((step, i) => (
            <React.Fragment key={step}>
              <div style={{
                padding: '0.625rem 1.25rem', borderRadius: '8px',
                backgroundColor: 'rgba(0,255,136,0.08)', border: '1px solid rgba(0,255,136,0.2)',
                fontSize: '0.8125rem', fontWeight: '600', color: '#00ff88',
              }}>
                {step}
              </div>
              {i < 4 && <ArrowRight size={16} color="#526352" />}
            </React.Fragment>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Pipelines;
