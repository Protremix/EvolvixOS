import React, { useState } from 'react';
import { GitCompare, Plus, Minus, Edit3, RefreshCw, AlertTriangle, CheckCircle, FileCode, Info } from 'lucide-react';
import astDiffService from '../services/astDiffService';

const ASTDiff = () => {
  const [oldCode, setOldCode] = useState('');
  const [newCode, setNewCode] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleCompare = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await astDiffService.compare(oldCode, newCode, 'python');
      setResult(data);
    } catch (e) {
      setError(e.response ? e.response.data.detail : 'Comparison failed');
    }
    setLoading(false);
  };

  const changeIcon = (type) => {
    switch (type) {
      case 'added': return <Plus size={16} color="#00ff88" />;
      case 'removed': return <Minus size={16} color="#ef4444" />;
      case 'modified': return <Edit3 size={16} color="#3b82f6" />;
      case 'renamed': return <RefreshCw size={16} color="#a855f7" />;
      case 'signature_changed': return <AlertTriangle size={16} color="#f59e0b" />;
      default: return <Info size={16} color="#8e9b8e" />;
    }
  };

  const changeColor = (type) => {
    switch (type) {
      case 'added': return 'rgba(0,255,136,0.1)';
      case 'removed': return 'rgba(239,68,68,0.1)';
      case 'modified': return 'rgba(59,130,246,0.1)';
      case 'renamed': return 'rgba(168,85,247,0.1)';
      case 'signature_changed': return 'rgba(245,158,11,0.1)';
      default: return 'rgba(139,152,139,0.1)';
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div>
        <h1 style={{ fontSize: '1.75rem', fontWeight: '800', color: '#f0fdf4' }}>AST-Aware Diff</h1>
        <p style={{ color: '#8e9b8e', marginTop: '0.25rem', fontSize: '0.875rem' }}>Semantic code comparison using Abstract Syntax Tree analysis</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
        <div>
          <label style={{ fontSize: '0.8125rem', color: '#8e9b8e', marginBottom: '0.375rem', display: 'block' }}>Old Version</label>
          <textarea value={oldCode} onChange={(e) => setOldCode(e.target.value)} placeholder="Paste old Python code..." style={{ width: '100%', minHeight: '200px', padding: '0.75rem', backgroundColor: '#0e140e', border: '1px solid #1f2e1f', borderRadius: '8px', color: '#f0fdf4', fontFamily: 'monospace', fontSize: '0.8125rem', resize: 'vertical', outline: 'none' }} />
        </div>
        <div>
          <label style={{ fontSize: '0.8125rem', color: '#8e9b8e', marginBottom: '0.375rem', display: 'block' }}>New Version</label>
          <textarea value={newCode} onChange={(e) => setNewCode(e.target.value)} placeholder="Paste new Python code..." style={{ width: '100%', minHeight: '200px', padding: '0.75rem', backgroundColor: '#0e140e', border: '1px solid #1f2e1f', borderRadius: '8px', color: '#f0fdf4', fontFamily: 'monospace', fontSize: '0.8125rem', resize: 'vertical', outline: 'none' }} />
        </div>
      </div>

      <button onClick={handleCompare} disabled={loading || !oldCode.trim() || !newCode.trim()} style={{ padding: '0.5rem 1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem', backgroundColor: loading || !oldCode.trim() || !newCode.trim() ? '#1f2e1f' : 'rgba(0,255,136,0.12)', border: loading || !oldCode.trim() || !newCode.trim() ? '1px solid #1f2e1f' : '1px solid rgba(0,255,136,0.3)', borderRadius: '8px', color: loading || !oldCode.trim() || !newCode.trim() ? '#526352' : '#00ff88', fontSize: '0.875rem', fontWeight: '600', cursor: loading || !oldCode.trim() || !newCode.trim() ? 'not-allowed' : 'pointer' }}>
        <GitCompare size={18} /> {loading ? 'Comparing...' : 'Compare AST'}
      </button>

      {error && (
        <div className="card" style={{ border: '1px solid rgba(239,68,68,0.3)' }}>
          <p style={{ color: '#ef4444', fontSize: '0.875rem' }}>{error}</p>
        </div>
      )}

      {result && (
        <>
          <div className="grid-4">
            <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
              <span style={{ fontSize: '0.8125rem', color: '#8e9b8e' }}>Total Changes</span>
              <span style={{ fontSize: '1.5rem', fontWeight: '800', color: '#f0fdf4' }}>{result.summary.total_changes}</span>
            </div>
            <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
              <span style={{ fontSize: '0.8125rem', color: '#8e9b8e' }}>Added</span>
              <span style={{ fontSize: '1.5rem', fontWeight: '800', color: '#00ff88' }}>{result.summary.added}</span>
            </div>
            <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
              <span style={{ fontSize: '0.8125rem', color: '#8e9b8e' }}>Removed</span>
              <span style={{ fontSize: '1.5rem', fontWeight: '800', color: '#ef4444' }}>{result.summary.removed}</span>
            </div>
            <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
              <span style={{ fontSize: '0.8125rem', color: '#8e9b8e' }}>Breaking</span>
              <span style={{ fontSize: '1.5rem', fontWeight: '800', color: result.summary.breaking ? '#ef4444' : '#00ff88' }}>{result.summary.breaking ? 'Yes' : 'No'}</span>
            </div>
          </div>

          {result.changes && result.changes.length > 0 && (
            <div className="card">
              <h2 style={{ fontSize: '1.1rem', fontWeight: '700', color: '#f0fdf4', marginBottom: '1rem' }}>Semantic Changes ({result.changes.length})</h2>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {result.changes.map((change, i) => (
                  <div key={i} style={{ padding: '0.5rem 0.75rem', backgroundColor: changeColor(change.change_type), border: '1px solid #1f2e1f', borderRadius: '8px', display: 'flex', alignItems: 'flex-start', gap: '0.5rem' }}>
                    {changeIcon(change.change_type)}
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: '0.8125rem', color: '#f0fdf4', fontWeight: '600' }}>{change.name || change.description}</div>
                      <div style={{ fontSize: '0.75rem', color: '#8e9b8e', marginTop: '0.25rem' }}>{change.description}</div>
                      {change.old_value && change.new_value && change.old_value !== change.new_value && (
                        <div style={{ marginTop: '0.375rem', display: 'flex', gap: '0.5rem', fontSize: '0.6875rem', fontFamily: 'monospace' }}>
                          <span style={{ color: '#ef4444' }}>{change.old_value}</span>
                          <span style={{ color: '#8e9b8e' }}>{'->'}</span>
                          <span style={{ color: '#00ff88' }}>{change.new_value}</span>
                        </div>
                      )}
                    </div>
                    {change.severity === 'critical' && <AlertTriangle size={14} color="#ef4444" />}
                    {change.severity === 'info' && <CheckCircle size={14} color="#00ff88" />}
                  </div>
                ))}
              </div>
            </div>
          )}

          {result.line_diff && result.line_diff.length > 0 && (
            <div className="card">
              <h2 style={{ fontSize: '1.1rem', fontWeight: '700', color: '#f0fdf4', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <FileCode size={20} color="#8e9b8e" /> Unified Diff
              </h2>
              <pre style={{ backgroundColor: '#0e140e', border: '1px solid #1f2e1f', borderRadius: '8px', padding: '1rem', overflow: 'auto', fontSize: '0.75rem', color: '#f0fdf4', fontFamily: 'monospace', maxHeight: '250px' }}>
                {result.line_diff.join('')}
              </pre>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default ASTDiff;
