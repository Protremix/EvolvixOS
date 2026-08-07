import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  GitBranch, GitCommit, GitPullRequest, CircleDot,
  CheckCircle, XCircle, Clock, AlertCircle, Search
} from 'lucide-react';
import githubService from '../services/githubService';

const DEFAULT_REPO = { owner: 'verdischain', repo: 'Verdis' };

const GitHub = () => {
  const [repoInput, setRepoInput] = useState('verdischain/Verdis');
  const [activeRepo, setActiveRepo] = useState(DEFAULT_REPO);

  const handleSearch = () => {
    const [owner, repo] = repoInput.split('/');
    if (owner && repo) setActiveRepo({ owner: owner.trim(), repo: repo.trim() });
  };

  const { data: repoInfo, isLoading: repoLoading } = useQuery({
    queryKey: ['github-repo', activeRepo.owner, activeRepo.repo],
    queryFn: () => githubService.getRepo(activeRepo.owner, activeRepo.repo),
    retry: 1,
  });

  const { data: issues } = useQuery({
    queryKey: ['github-issues', activeRepo.owner, activeRepo.repo],
    queryFn: () => githubService.listIssues(activeRepo.owner, activeRepo.repo),
    refetchInterval: 60000,
    retry: 1,
  });

  const { data: prs } = useQuery({
    queryKey: ['github-prs', activeRepo.owner, activeRepo.repo],
    queryFn: () => githubService.listPRs(activeRepo.owner, activeRepo.repo),
    refetchInterval: 60000,
    retry: 1,
  });

  const { data: commits } = useQuery({
    queryKey: ['github-commits', activeRepo.owner, activeRepo.repo],
    queryFn: () => githubService.listCommits(activeRepo.owner, activeRepo.repo, 10),
    refetchInterval: 30000,
    retry: 1,
  });

  const { data: workflowRuns } = useQuery({
    queryKey: ['github-runs', activeRepo.owner, activeRepo.repo],
    queryFn: () => githubService.listWorkflowRuns(activeRepo.owner, activeRepo.repo, 10),
    refetchInterval: 30000,
    retry: 1,
  });

  const getStatusIcon = (conclusion) => {
    if (conclusion === 'success') return <CheckCircle size={14} color="#00ff88" />;
    if (conclusion === 'failure') return <XCircle size={14} color="#ef4444" />;
    if (conclusion === 'cancelled') return <XCircle size={14} color="#8e9b8e" />;
    return <Clock size={14} color="#f59e0b" />;
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Header with Search */}
      <div>
        <h1 style={{ fontSize: '1.75rem', fontWeight: '800', color: '#f0fdf4' }}>
          GitHub Integration
        </h1>
        <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.75rem' }}>
          <input
            type="text"
            value={repoInput}
            onChange={(e) => setRepoInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            placeholder="owner/repo (e.g. verdischain/Verdis)"
            style={{
              flex: 1, padding: '0.5rem 0.75rem',
              backgroundColor: '#0e140e', border: '1px solid #1f2e1f',
              borderRadius: '8px', color: '#f0fdf4', fontSize: '0.875rem',
              outline: 'none',
            }}
          />
          <button
            onClick={handleSearch}
            style={{
              padding: '0.5rem 1rem', backgroundColor: 'rgba(0,255,136,0.12)',
              border: '1px solid rgba(0,255,136,0.3)', borderRadius: '8px',
              color: '#00ff88', fontSize: '0.875rem', fontWeight: '600',
              cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.375rem',
            }}
          >
            <Search size={16} /> Search
          </button>
        </div>
      </div>

      {/* Repo Info */}
      {repoInfo && (
        <div className="card" style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{
            width: 48, height: 48, borderRadius: 12,
            backgroundColor: 'rgba(59,130,246,0.15)', border: '1px solid rgba(59,130,246,0.3)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <GitBranch size={24} color="#3b82f6" />
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: '1.1rem', fontWeight: '700', color: '#f0fdf4' }}>
              {repoInfo.full_name}
            </div>
            <div style={{ fontSize: '0.8125rem', color: '#8e9b8e' }}>
              {repoInfo.description || 'No description'}
              {repoInfo.language && ` · ${repoInfo.language}`}
              {repoInfo.stargazers_count !== undefined && ` · ⭐ ${repoInfo.stargazers_count}`}
            </div>
          </div>
        </div>
      )}

      {/* Stats Grid */}
      <div className="grid-4">
        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '0.875rem', color: '#8e9b8e' }}>Open Issues</span>
            <CircleDot size={16} color="#f59e0b" />
          </div>
          <div style={{ fontSize: '1.5rem', fontWeight: '800', color: '#f0fdf4' }}>
            {issues?.length ?? '—'}
          </div>
        </div>
        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '0.875rem', color: '#8e9b8e' }}>Open PRs</span>
            <GitPullRequest size={16} color="#a855f7" />
          </div>
          <div style={{ fontSize: '1.5rem', fontWeight: '800', color: '#f0fdf4' }}>
            {prs?.length ?? '—'}
          </div>
        </div>
        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '0.875rem', color: '#8e9b8e' }}>Recent Commits</span>
            <GitCommit size={16} color="#3b82f6" />
          </div>
          <div style={{ fontSize: '1.5rem', fontWeight: '800', color: '#f0fdf4' }}>
            {commits?.length ?? '—'}
          </div>
        </div>
        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '0.875rem', color: '#8e9b8e' }}>CI Runs</span>
            <Clock size={16} color="#06b6d4" />
          </div>
          <div style={{ fontSize: '1.5rem', fontWeight: '800', color: '#f0fdf4' }}>
            {workflowRuns?.length ?? '—'}
          </div>
        </div>
      </div>

      {/* CI/CD Runs */}
      <div className="card">
        <h2 style={{ fontSize: '1.1rem', fontWeight: '700', color: '#f0fdf4', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <AlertCircle size={18} color="#06b6d4" />
          Recent CI/CD Runs
        </h2>
        {workflowRuns && workflowRuns.length > 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.375rem' }}>
            {workflowRuns.slice(0, 8).map((run, i) => (
              <div key={i} style={{
                display: 'flex', alignItems: 'center', gap: '0.5rem',
                padding: '0.5rem 0.75rem', backgroundColor: '#0e140e',
                border: '1px solid #1f2e1f', borderRadius: '8px',
              }}>
                {getStatusIcon(run.conclusion)}
                <span style={{ fontSize: '0.8125rem', color: '#f0fdf4', flex: 1 }}>
                  {run.name || `Run ${run.id}`}
                </span>
                <span style={{ fontSize: '0.6875rem', color: '#8e9b8e' }}>
                  {run.head_branch}
                </span>
                <span style={{
                  fontSize: '0.6875rem', fontWeight: '600', textTransform: 'capitalize',
                  color: run.conclusion === 'success' ? '#00ff88' : run.conclusion === 'failure' ? '#ef4444' : '#8e9b8e',
                }}>
                  {run.conclusion || run.status}
                </span>
              </div>
            ))}
          </div>
        ) : (
          <p style={{ color: '#526352', fontSize: '0.875rem' }}>No CI runs available.</p>
        )}
      </div>

      {/* Recent Commits */}
      <div className="card">
        <h2 style={{ fontSize: '1.1rem', fontWeight: '700', color: '#f0fdf4', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <GitCommit size={18} color="#3b82f6" />
          Recent Commits
        </h2>
        {commits && commits.length > 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.375rem' }}>
            {commits.slice(0, 6).map((commit, i) => (
              <div key={i} style={{
                display: 'flex', alignItems: 'center', gap: '0.5rem',
                padding: '0.5rem 0.75rem', backgroundColor: '#0e140e',
                border: '1px solid #1f2e1f', borderRadius: '8px',
              }}>
                <span style={{
                  fontSize: '0.6875rem', fontFamily: 'monospace', color: '#00ff88',
                  backgroundColor: 'rgba(0,255,136,0.1)', padding: '0.125rem 0.375rem',
                  borderRadius: '4px',
                }}>
                  {commit.sha?.substring(0, 7)}
                </span>
                <span style={{ fontSize: '0.8125rem', color: '#f0fdf4', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {commit.commit?.message?.split('\n')[0]}
                </span>
                <span style={{ fontSize: '0.6875rem', color: '#8e9b8e' }}>
                  {commit.commit?.author?.name}
                </span>
              </div>
            ))}
          </div>
        ) : (
          <p style={{ color: '#526352', fontSize: '0.875rem' }}>No commits available.</p>
        )}
      </div>
    </div>
  );
};

export default GitHub;
