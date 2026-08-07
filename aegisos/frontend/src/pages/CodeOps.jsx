import React, { useState } from 'react';
import {
  FlaskConical, Stethoscope, Code, FileCode, Bug, CheckCircle,
  AlertTriangle, Wrench, Activity
} from 'lucide-react';
import codeOpsService from '../services/codeOpsService';

const CodeOps = () => {
  const [activeTab, setActiveTab] = useState('test-gen');
  const [sourceCode, setSourceCode] = useState('');
  const [testResult, setTestResult] = useState(null);
  const [ciLogs, setCiLogs] = useState('');
  const [ciResult, setCiResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleGenerateTests = async () => {
    setLoading(true);
    setTestResult(null);
    try {
      const result = await codeOpsService.generateTests({
        source_code: sourceCode,
        language: 'python',
        file_name: 'module.py',
      });
      setTestResult(result);
    } catch (e) {
      setTestResult({ error: e.response?.data?.detail || 'Generation failed' });
    }
    setLoading(false);
  };

  const handleDiagnoseCI = async () => {
    setLoading(true);
    setCiResult(null);
    try {
      const result = await codeOpsService.diagnoseCI({
        error_logs: ciLogs,
        generate_fix: true,
      });
      setCiResult(result);
    } catch (e) {
      setCiResult({ error: e.response?.data?.detail || 'Diagnosis failed' });
    }
    setLoading(false);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div>
        <h1 style={{ fontSize: '1.75rem', fontWeight: '800', color: '#f0fdf4' }}>
          Code Operations
        </h1>
        <p style={{ color: '#8e9b8e', marginTop: '0.25rem', fontSize: '0.875rem' }}>
          Automated test generation & self-healing CI/CD pipeline
        </p>
      </div>

      {/* Tab Switcher */}
      <div style={{ display: 'flex', gap: '0.5rem' }}>
        <button
          onClick={() => setActiveTab('test-gen')}
          style={{
            display: 'flex', alignItems: 'center', gap: '0.5rem',
            padding: '0.5rem 1rem', borderRadius: '8px',
            fontSize: '0.875rem', fontWeight: '600', cursor: 'pointer',
            backgroundColor: activeTab === 'test-gen' ? 'rgba(0,255,136,0.12)' : '#0e140e',
            border: activeTab === 'test-gen' ? '1px solid rgba(0,255,136,0.3)' : '1px solid #1f2e1f',
            color: activeTab === 'test-gen' ? '#00ff88' : '#8e9b8e',
          }}
        >
          <FlaskConical size={16} /> Test Generation
        </button>
        <button
          onClick={() => setActiveTab('ci-healer')}
          style={{
            display: 'flex', alignItems: 'center', gap: '0.5rem',
            padding: '0.5rem 1rem', borderRadius: '8px',
            fontSize: '0.875rem', fontWeight: '600', cursor: 'pointer',
            backgroundColor: activeTab === 'ci-healer' ? 'rgba(239,68,68,0.12)' : '#0e140e',
            border: activeTab === 'ci-healer' ? '1px solid rgba(239,68,68,0.3)' : '1px solid #1f2e1f',
            color: activeTab === 'ci-healer' ? '#ef4444' : '#8e9b8e',
          }}
        >
          <Stethoscope size={16} /> CI/CD Healer
        </button>
      </div>

      {/* Test Generation Tab */}
      {activeTab === 'test-gen' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div className="card">
            <h2 style={{ fontSize: '1.1rem', fontWeight: '700', color: '#f0fdf4', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Code size={20} color="#00ff88" /> Source Code Input
            </h2>
            <textarea
              value={sourceCode}
              onChange={(e) => setSourceCode(e.target.value)}
              placeholder="Paste Python source code here..."
              style={{
                width: '100%', minHeight: '180px', padding: '0.75rem',
                backgroundColor: '#0e140e', border: '1px solid #1f2e1f',
                borderRadius: '8px', color: '#f0fdf4', fontFamily: 'monospace',
                fontSize: '0.8125rem', resize: 'vertical', outline: 'none',
              }}
            />
            <button
              onClick={handleGenerateTests}
              disabled={loading || !sourceCode.trim()}
              style={{
                marginTop: '0.75rem', padding: '0.5rem 1.5rem',
                backgroundColor: loading || !sourceCode.trim() ? '#1f2e1f' : 'rgba(0,255,136,0.15)',
                border: loading || !sourceCode.trim() ? '1px solid #1f2e1f' : '1px solid rgba(0,255,136,0.3)',
                borderRadius: '8px', color: loading || !sourceCode.trim() ? '#526352' : '#00ff88',
                fontSize: '0.875rem', fontWeight: '600', cursor: loading || !sourceCode.trim() ? 'not-allowed' : 'pointer',
              }}
            >
              {loading ? 'Generating...' : 'Generate Tests'}
            </button>
          </div>

          {testResult && !testResult.error && (
            <div className="card">
              <h2 style={{ fontSize: '1.1rem', fontWeight: '700', color: '#f0fdf4', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <CheckCircle size={20} color="#00ff88" />
                Generated: {testResult.test_file} ({testResult.test_count} tests)
              </h2>
              <pre style={{
                backgroundColor: '#0e140e', border: '1px solid #1f2e1f', borderRadius: '8px',
                padding: '1rem', overflow: 'auto', fontSize: '0.8125rem', color: '#f0fdf4',
                fontFamily: 'monospace', maxHeight: '300px',
              }}>
                {testResult.test_code}
              </pre>
            </div>
          )}

          {testResult?.error && (
            <div className="card" style={{ border: '1px solid rgba(239,68,68,0.3)' }}>
              <p style={{ color: '#ef4444', fontSize: '0.875rem' }}>Error: {testResult.error}</p>
            </div>
          )}
        </div>
      )}

      {/* CI Healer Tab */}
      {activeTab === 'ci-healer' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div className="card">
            <h2 style={{ fontSize: '1.1rem', fontWeight: '700', color: '#f0fdf4', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Bug size={20} color="#ef4444" /> CI/CD Error Logs
            </h2>
            <textarea
              value={ciLogs}
              onChange={(e) => setCiLogs(e.target.value)}
              placeholder="Paste CI/CD error logs here..."
              style={{
                width: '100%', minHeight: '180px', padding: '0.75rem',
                backgroundColor: '#0e140e', border: '1px solid #1f2e1f',
                borderRadius: '8px', color: '#f0fdf4', fontFamily: 'monospace',
                fontSize: '0.8125rem', resize: 'vertical', outline: 'none',
              }}
            />
            <button
              onClick={handleDiagnoseCI}
              disabled={loading || !ciLogs.trim()}
              style={{
                marginTop: '0.75rem', padding: '0.5rem 1.5rem',
                backgroundColor: loading || !ciLogs.trim() ? '#1f2e1f' : 'rgba(239,68,68,0.15)',
                border: loading || !ciLogs.trim() ? '1px solid #1f2e1f' : '1px solid rgba(239,68,68,0.3)',
                borderRadius: '8px', color: loading || !ciLogs.trim() ? '#526352' : '#ef4444',
                fontSize: '0.875rem', fontWeight: '600', cursor: loading || !ciLogs.trim() ? 'not-allowed' : 'pointer',
              }}
            >
              {loading ? 'Diagnosing...' : 'Diagnose & Fix'}
            </button>
          </div>

          {ciResult && !ciResult.error && ciResult.diagnosis && (
            <div className="card">
              <h2 style={{ fontSize: '1.1rem', fontWeight: '700', color: '#f0fdf4', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Stethoscope size={20} color="#f59e0b" /> Diagnosis
              </h2>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
                  <span style={{
                    padding: '0.25rem 0.75rem', borderRadius: '6px', fontSize: '0.75rem', fontWeight: '600',
                    backgroundColor: ciResult.diagnosis.failure_type === 'import' ? 'rgba(59,130,246,0.15)' :
                      ciResult.diagnosis.failure_type === 'syntax' ? 'rgba(239,68,68,0.15)' :
                      ciResult.diagnosis.failure_type === 'test' ? 'rgba(245,158,11,0.15)' :
                      'rgba(139,152,139,0.15)',
                    color: ciResult.diagnosis.failure_type === 'import' ? '#3b82f6' :
                      ciResult.diagnosis.failure_type === 'syntax' ? '#ef4444' :
                      ciResult.diagnosis.failure_type === 'test' ? '#f59e0b' : '#8e9b8e',
                    textTransform: 'capitalize',
                  }}>
                    {ciResult.diagnosis.failure_type}
                  </span>
                  <span style={{
                    fontSize: '0.75rem', fontWeight: '600',
                    color: ciResult.diagnosis.confidence >= 0.8 ? '#00ff88' : '#f59e0b',
                  }}>
                    {(ciResult.diagnosis.confidence * 100).toFixed(0)}% confidence
                  </span>
                </div>
                <div style={{ padding: '0.5rem 0', borderTop: '1px solid #1f2e1f' }}>
                  <span style={{ fontSize: '0.8125rem', color: '#8e9b8e' }}>Root Cause: </span>
                  <span style={{ fontSize: '0.8125rem', color: '#f0fdf4' }}>{ciResult.diagnosis.root_cause}</span>
                </div>
                <div style={{ padding: '0.5rem 0', borderTop: '1px solid #1f2e1f' }}>
                  <span style={{ fontSize: '0.8125rem', color: '#8e9b8e' }}>Suggested Fix: </span>
                  <span style={{ fontSize: '0.8125rem', color: '#00ff88' }}>{ciResult.diagnosis.suggested_fix}</span>
                </div>
                {ciResult.diagnosis.affected_files?.length > 0 && (
                  <div style={{ padding: '0.5rem 0', borderTop: '1px solid #1f2e1f' }}>
                    <span style={{ fontSize: '0.8125rem', color: '#8e9b8e' }}>Affected: </span>
                    {ciResult.diagnosis.affected_files.map((f, i) => (
                      <code key={i} style={{ fontSize: '0.75rem', color: '#f0fdf4', marginLeft: '0.375rem' }}>{f}</code>
                    ))}
                  </div>
                )}
              </div>

              {ciResult.fix && ciResult.fix.fix_summary && (
                <div style={{ marginTop: '1rem', padding: '0.75rem', backgroundColor: 'rgba(0,255,136,0.05)', borderRadius: '8px', border: '1px solid rgba(0,255,136,0.2)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                    <Wrench size={16} color="#00ff88" />
                    <span style={{ fontSize: '0.875rem', fontWeight: '600', color: '#00ff88' }}>Auto-Fix Generated</span>
                  </div>
                  <p style={{ fontSize: '0.8125rem', color: '#f0fdf4' }}>{ciResult.fix.fix_summary}</p>
                  {ciResult.fix.patched_files && Object.keys(ciResult.fix.patched_files).length > 0 && (
                    <div style={{ marginTop: '0.5rem' }}>
                      {Object.entries(ciResult.fix.patched_files).map(([fname, content]) => (
                        <div key={fname} style={{ marginTop: '0.5rem' }}>
                          <code style={{ fontSize: '0.75rem', color: '#00ff88' }}>{fname}</code>
                          <pre style={{
                            marginTop: '0.25rem', padding: '0.5rem',
                            backgroundColor: '#0e140e', borderRadius: '4px',
                            fontSize: '0.75rem', color: '#f0fdf4', fontFamily: 'monospace',
                            maxHeight: '200px', overflow: 'auto',
                          }}>
                            {content}
                          </pre>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {ciResult?.error && (
            <div className="card" style={{ border: '1px solid rgba(239,68,68,0.3)' }}>
              <p style={{ color: '#ef4444', fontSize: '0.875rem' }}>Error: {ciResult.error}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default CodeOps;
