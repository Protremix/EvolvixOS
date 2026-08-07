import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  ArrowLeft, Bot, Activity, CheckCircle, Star, MessageSquare,
  TrendingUp, Zap, Clock, Cpu
} from 'lucide-react';
import aiService from '../services/aiService';
import feedbackService from '../services/feedbackService';

const AgentDetail = () => {
  const { name } = useParams();
  const decodedName = decodeURIComponent(name);

  const { data: agents = [] } = useQuery({
    queryKey: ['ai-agents'],
    queryFn: aiService.getAgents,
    refetchInterval: 10000,
  });

  const { data: improvements } = useQuery({
    queryKey: ['agent-improvements', decodedName],
    queryFn: () => feedbackService.getImprovements(decodedName),
    retry: false,
  });

  const { data: feedback = [] } = useQuery({
    queryKey: ['agent-feedback', decodedName],
    queryFn: () => feedbackService.getByAgent(decodedName),
    retry: false,
  });

  const agent = agents.find(a => (a.name || '') === decodedName || a.display_name === decodedName);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Back link */}
      <Link to="/agents" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem', color: '#8e9b8e', textDecoration: 'none', fontSize: '0.875rem' }}>
        <ArrowLeft size={16} />
        <span>Back to Agents</span>
      </Link>

      {/* Agent Header */}
      <div style={{
        backgroundColor: '#121812', border: '1px solid #1f2e1f', borderRadius: '16px',
        padding: '2rem', display: 'flex', alignItems: 'center', gap: '1.5rem', flexWrap: 'wrap',
      }}>
        <div style={{
          width: 64, height: 64, borderRadius: 16,
          backgroundColor: 'rgba(0,255,136,0.15)', border: '1px solid rgba(0,255,136,0.3)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <Bot size={32} color="#00ff88" />
        </div>
        <div style={{ flex: 1, minWidth: 200 }}>
          <h1 style={{ fontSize: '1.75rem', fontWeight: '800', color: '#f0fdf4', margin: 0 }}>
            {agent?.display_name || decodedName}
          </h1>
          <p style={{ color: '#8e9b8e', marginTop: '0.25rem' }}>
            {agent?.description || 'AI Agent in the EvolvixOS swarm'}
          </p>
        </div>
        <div style={{
          display: 'inline-flex', alignItems: 'center', gap: '0.375rem',
          padding: '0.5rem 1rem', borderRadius: '9999px',
          backgroundColor: agent?.status === 'active' ? 'rgba(0,255,136,0.12)' : 'rgba(142,155,142,0.12)',
          border: agent?.status === 'active' ? '1px solid rgba(0,255,136,0.25)' : '1px solid rgba(142,155,142,0.25)',
          color: agent?.status === 'active' ? '#00ff88' : '#8e9b8e',
          fontSize: '0.8125rem', fontWeight: '600',
        }}>
          <Activity size={14} />
          <span style={{ textTransform: 'capitalize' }}>{agent?.status || 'idle'}</span>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid-4">
        <div className="card" style={{ textAlign: 'center' }}>
          <CheckCircle size={20} color="#00ff88" style={{ margin: '0 auto 0.5rem' }} />
          <div style={{ fontSize: '1.75rem', fontWeight: '800', color: '#f0fdf4' }}>
            {agent?.tasks_completed || 0}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#8e9b8e' }}>Tasks Completed</div>
        </div>
        <div className="card" style={{ textAlign: 'center' }}>
          <Star size={20} color="#f59e0b" style={{ margin: '0 auto 0.5rem' }} />
          <div style={{ fontSize: '1.75rem', fontWeight: '800', color: '#f0fdf4' }}>
            {improvements?.average_rating?.toFixed(1) || '—'}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#8e9b8e' }}>Avg Rating</div>
        </div>
        <div className="card" style={{ textAlign: 'center' }}>
          <MessageSquare size={20} color="#3b82f6" style={{ margin: '0 auto 0.5rem' }} />
          <div style={{ fontSize: '1.75rem', fontWeight: '800', color: '#f0fdf4' }}>
            {improvements?.total_feedback || 0}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#8e9b8e' }}>Feedback Count</div>
        </div>
        <div className="card" style={{ textAlign: 'center' }}>
          <Cpu size={20} color="#a855f7" style={{ margin: '0 auto 0.5rem' }} />
          <div style={{ fontSize: '1.75rem', fontWeight: '800', color: '#f0fdf4' }}>
            {agent?.model || 'GPT-4o'}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#8e9b8e' }}>LLM Model</div>
        </div>
      </div>

      {/* Feedback & Improvements */}
      <div className="grid-2">
        {/* Improvement Summary */}
        <div className="card">
          <h2 style={{ fontSize: '1.1rem', fontWeight: '700', color: '#f0fdf4', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <TrendingUp size={20} color="#00ff88" />
            Improvement Summary
          </h2>
          {improvements && improvements.total_feedback > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.875rem', color: '#8e9b8e' }}>Average Rating</span>
                <span style={{ fontSize: '1.25rem', fontWeight: '700', color: '#00ff88' }}>
                  {improvements.average_rating.toFixed(2)}/5
                </span>
              </div>
              {/* Rating Distribution */}
              <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'flex-end', height: 60 }}>
                {[5, 4, 3, 2, 1].map(star => {
                  const count = improvements.rating_distribution?.[star] || 0;
                  const maxCount = Math.max(...Object.values(improvements.rating_distribution || {1:1}), 1);
                  const height = (count / maxCount) * 100;
                  return (
                    <div key={star} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.25rem' }}>
                      <div style={{ flex: 1, width: '100%', display: 'flex', alignItems: 'flex-end' }}>
                        <div style={{
                          width: '100%', height: `${height}%`, minHeight: count > 0 ? '8px' : '2px',
                          backgroundColor: star >= 4 ? '#00ff88' : star === 3 ? '#f59e0b' : '#ef4444',
                          borderRadius: '4px 4px 0 0', opacity: count > 0 ? 1 : 0.2,
                        }} />
                      </div>
                      <span style={{ fontSize: '0.6875rem', color: '#526352' }}>{star}★</span>
                    </div>
                  );
                })}
              </div>
              {/* Common Corrections */}
              {improvements.common_corrections?.length > 0 && (
                <div style={{ marginTop: '0.5rem' }}>
                  <div style={{ fontSize: '0.8125rem', color: '#8e9b8e', marginBottom: '0.5rem' }}>Common Corrections:</div>
                  {improvements.common_corrections.map((c, i) => (
                    <div key={i} style={{
                      padding: '0.625rem', backgroundColor: '#0e140e',
                      border: '1px solid #1f2e1f', borderRadius: '8px',
                      fontSize: '0.8125rem', color: '#f0fdf4', marginBottom: '0.375rem',
                    }}>
                      {c}
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <p style={{ color: '#526352', fontSize: '0.875rem' }}>No feedback data yet for this agent.</p>
          )}
        </div>

        {/* Recent Feedback */}
        <div className="card">
          <h2 style={{ fontSize: '1.1rem', fontWeight: '700', color: '#f0fdf4', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <MessageSquare size={20} color="#3b82f6" />
            Recent Feedback
          </h2>
          {feedback && feedback.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {feedback.slice(0, 5).map((fb, i) => (
                <div key={i} style={{
                  padding: '0.875rem', backgroundColor: '#0e140e',
                  border: '1px solid #1f2e1f', borderRadius: '8px',
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.375rem' }}>
                    <div style={{ display: 'flex', gap: '0.125rem' }}>
                      {[1,2,3,4,5].map(s => (
                        <Star key={s} size={12} color={s <= fb.rating ? '#f59e0b' : '#1f2e1f'} fill={s <= fb.rating ? '#f59e0b' : 'none'} />
                      ))}
                    </div>
                    <span style={{ fontSize: '0.6875rem', color: '#526352' }}>
                      {fb.task_type || 'unknown'}
                    </span>
                  </div>
                  {fb.correction && (
                    <p style={{ fontSize: '0.8125rem', color: '#8e9b8e', margin: 0 }}>
                      {fb.correction}
                    </p>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p style={{ color: '#526352', fontSize: '0.875rem' }}>No feedback submitted yet.</p>
          )}
        </div>
      </div>

      {/* Supported Task Types */}
      {agent?.supported_types && agent.supported_types.length > 0 && (
        <div className="card">
          <h2 style={{ fontSize: '1.1rem', fontWeight: '700', color: '#f0fdf4', marginBottom: '1rem' }}>
            Supported Task Types ({agent.supported_types.length})
          </h2>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
            {agent.supported_types.map((type, i) => (
              <div key={i} style={{
                padding: '0.375rem 0.875rem', borderRadius: '9999px',
                backgroundColor: 'rgba(0,255,136,0.08)', border: '1px solid rgba(0,255,136,0.2)',
                fontSize: '0.75rem', fontWeight: '500', color: '#00ff88',
              }}>
                {type}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default AgentDetail;
