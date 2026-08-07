import React, { useState } from 'react';
import {
  GitBranch, Network, AlertTriangle, Search, Trash2,
  Download, TrendingUp, FileCode, RefreshCw
} from 'lucide-react';
import depGraphService from '../services/depGraphService';

const DependencyGraphPage = () => {
  const [projectPath, setProjectPath] = useState('');
  const [graphData, setGraphData] = useState(null);
  const [stats, setStats] = useState(null);
  const [cycles, setCycles] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleBuild = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await depGraphService.build(projectPath);
      setGraphData(result);
      setStats(result.stats);
      setCycles(result.cycles);
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to build graph');
    }
    setLoading(false);
  };

  const handleClearCache = async () => {
    try {
      await depGraphService.clearCache(projectPath);
      setGraphData(null);
      setStats(null);
      setCycles(null);
    } catch (e) {
      setError('Failed to clear cache');
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div>
        <h1 style={{ fontSize: '1.75rem', fontWeight: '800', color: '#f0fdf4' }}>
          Dependency Graph
        </h1>
        <p style={{ color: '#8e9b8e', marginTop: '0.25rem', fontSize: '0.875rem' }}>
          Track import relationships, detect circular deps, analyze change impact
        </p>
      </div>

      {/* Search */}
      <div style={{ display: 'flex', gap: '0.5rem' }}>
        <input
          type="text"
          value={projectPath}
          onChange={(e) => setProjectPath(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleBuild()}
          placeholder="Project root path (e.g. /app/my-project)"
          style={{
            flex: 1, padding: '0.5rem 0.75rem',
            backgroundColor: '#0e140e', border: '1px solid #1f2e1f',
            borderRadius: '8px', color: '#f0fdf4', fontSize: '0.875rem',
            fontFamily: 'monospace', outline: 'none',
          }}
        />
        <button
          onClick={handleBuild}
          disabled={loading || !projectPath.trim()}
          style={{
            padding: '0.5rem 1rem', display: 'flex', alignItems: 'center', gap: '0.375rem',
            backgroundColor: loading || !projectPath.trim() ? '#1f2e1f' : 'rgba(0,255,136,0.12)',
            border: loading || !projectPath.trim() ? '1px solid #1f2e1f' : '1px solid rgba(0,255,136,0.3)',
            borderRadius: '8px', color: loading || !projectPath.trim() ? '#526352' : '#00ff88',
            fontSize: '0.875rem', fontWeight: '600', cursor: loading || !projectPath.trim() ? 'not-allowed' : 'pointer',
          }}
        >
          <Search size={16} /> {loading ? 'Scanning...' : 'Analyze'}
        </button>
        {graphData && (
          <button
            onClick={handleClearCache}
            style={{
              padding: '0.5rem 1rem', display: 'flex', alignItems: 'center', gap: '0.375rem',
              backgroundColor: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.2)',
              borderRadius: '8px', color: '#ef4444', fontSize: '0.875rem', fontWeight: '600', cursor: 'pointer',
            }}
          >
            <Trash2 size={16} /> Clear
          </button>
        )}
      </div>

      {error && (
        <div className="card" style={{ border: '1px solid rgba(239,68,68,0.3)' }}>
          <p style={{ color: '#ef4444', fontSize: '0.875rem' }}>Error: {error}</p>
        </div>
      )}

      {/* Stats */}
      {stats && (
        <>
          <div className="grid-4">
            <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ fontSize: '0.875rem', color: '#8e9b8e' }}>Total Files</span>
                <FileCode size={16} color="#3b82f6" />
              </div>
              <div style={{ fontSize: '1.5rem', fontWeight: '800', color: '#f0fdf4' }}>
                {stats.total_files}
              </div>
            </div>
            <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ fontSize: '0.875rem', color: '#8e9b8e' }}>Dependencies</span>
                <GitBranch size={16} color="#00ff88" />
              </div>
              <div style={{ fontSize: '1.5rem', fontWeight: '800', color: '#f0fdf4' }}>
                {stats.total_dependencies}
              </div>
            </div>
            <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ fontSize: '0.875rem', color: '#8e9b8e' }}>Avg Deps/File</span>
                <TrendingUp size={16} color="#a855f7" />
              </div>
              <div style={{ fontSize: '1.5rem', fontWeight: '800', color: '#f0fdf4' }}>
                {stats.avg_dependencies_per_file}
              </div>
            </div>
            <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ fontSize: '0.875rem', color: '#8e9b8e' }}>Entry Points</span>
                <Network size={16} color="#f59e0b" />
              </div>
              <div style={{ fontSize: '1.5rem', fontWeight: '800', color: '#f0fdf4' }}>
                {stats.entry_points?.length || 0}
              </div>
            </div>
          </div>

          {/* Circular Dependencies */}
          {cycles && cycles.length > 0 && (
            <div className="card">
              <h2 style={{ fontSize: '1.1rem', fontWeight: '700', color: '#f0fdf4', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <AlertTriangle size={20} color="#ef4444" />
                Circular Dependencies ({cycles.length})
              </h2>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {cycles.map((cycle, i) => (
                  <div key={i} style={{
                    padding: '0.5rem 0.75rem', backgroundColor: '#0e140e',
                    border: '1px solid rgba(239,68,68,0.2)', borderRadius: '8px',
                    display: 'flex', alignItems: 'center', gap: '0.5rem',
                  }}>
                    <span style={{
                      fontSize: '0.6875rem', fontWeight: '600', textTransform: 'uppercase',
                      padding: '0.125rem 0.5rem', borderRadius: '4px',
                      backgroundColor: cycle.severity === 'critical' ? 'rgba(239,68,68,0.15)' : 'rgba(245,158,11,0.15)',
                      color: cycle.severity === 'critical' ? '#ef4444' : '#f59e0b',
                    }}>
                      {cycle.severity}
                    </span>
                    <span style={{ fontSize: '0.8125rem', color: '#f0fdf4', fontFamily: 'monospace' }}>
                      {cycle.cycle.join(' → ')}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Most Depended On */}
          {stats.most_depended_on?.length > 0 && (
            <div className="card">
              <h2 style={{ fontSize: '1.1rem', fontWeight: '700', color: '#f0fdf4', marginBottom: '1rem' }}>
                Most Depended On
              </h2>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.375rem' }}>
                {stats.most_depended_on.map((item, i) => (
                  <div key={i} style={{
                    display: 'flex', alignItems: 'center', gap: '0.5rem',
                    padding: '0.375rem 0.75rem', backgroundColor: '#0e140e',
                    border: '1px solid #1f2e1f', borderRadius: '8px',
                  }}>
                    <span style={{ fontSize: '0.8125rem', color: '#f0fdf4', flex: 1, fontFamily: 'monospace', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {item.file.split('/').pop()}
                    </span>
                    <span style={{
                      fontSize: '0.75rem', fontWeight: '600', color: '#00ff88',
                      backgroundColor: 'rgba(0,255,136,0.1)', padding: '0.125rem 0.5rem', borderRadius: '4px',
                    }}>
                      {item.dependents} dependents
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Most Imports */}
          {stats.most_dependencies?.length > 0 && (
            <div className="card">
              <h2 style={{ fontSize: '1.1rem', fontWeight: '700', color: '#f0fdf4', marginBottom: '1rem' }}>
                Most Imports
              </h2>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.375rem' }}>
                {stats.most_dependencies.map((item, i) => (
                  <div key={i} style={{
                    display: 'flex', alignItems: 'center', gap: '0.5rem',
                    padding: '0.375rem 0.75rem', backgroundColor: '#0e140e',
                    border: '1px solid #1f2e1f', borderRadius: '8px',
                  }}>
                    <span style={{ fontSize: '0.8125rem', color: '#f0fdf4', flex: 1, fontFamily: 'monospace', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {item.file.split('/').pop()}
                    </span>
                    <span style={{
                      fontSize: '0.75rem', fontWeight: '600', color: '#3b82f6',
                      backgroundColor: 'rgba(59,130,246,0.1)', padding: '0.125rem 0.5rem', borderRadius: '4px',
                    }}>
                      {item.imports} imports
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default DependencyGraphPage;
