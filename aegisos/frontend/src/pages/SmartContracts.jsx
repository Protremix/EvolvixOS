import React, { useState, useEffect, useCallback } from 'react';
import smartContractService from '../services/smartContractService';

function SmartContracts() {
  const [tab, setTab] = useState('templates');
  const [templates, setTemplates] = useState([]);
  const [scans, setScans] = useState([]);
  const [contracts, setContracts] = useState([]);
  const [stats, setStats] = useState(null);
  const [scanInput, setScanInput] = useState('');
  const [scanResult, setScanResult] = useState(null);
  const [selectedTemplate, setSelectedTemplate] = useState(null);

  const fetchAll = useCallback(async () => {
    try {
      const [t, s, c, st] = await Promise.all([
        smartContractService.listTemplates(),
        smartContractService.listScans(20),
        smartContractService.listContracts({}),
        smartContractService.stats(),
      ]);
      setTemplates(t.data || []);
      setScans(s.data || []);
      setContracts(c.data || []);
      setStats(st.data || {});
    } catch (err) { console.error(err); }
  }, []);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  const handleScan = async () => {
    try {
      const r = await smartContractService.scan({ source_code: scanInput, contract_name: 'Manual' });
      setScanResult(r.data);
      fetchAll();
    } catch (e) { console.error(e); }
  };

  const sevColor = { critical: '#EF4444', high: '#F97316', medium: '#FFA500', low: '#FFD700', info: '#4F46E5' };
  const panel = { background: '#1A1A1E', borderRadius: '10px', border: '1px solid #333', padding: '14px' };
  const btn = { padding: '8px 16px', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '13px', color: '#fff' };
  const input = { padding: '8px 12px', background: '#0D0D0F', border: '1px solid #333', borderRadius: '6px', color: '#fff', fontSize: '13px', width: '100%' };

  return (
    <div style={{ padding: '24px' }}>
      <h1 style={{ fontSize: '28px', fontWeight: 700, marginBottom: '4px' }}>📜 Smart Contracts</h1>
      <p style={{ color: '#888', marginBottom: '20px' }}>Templates, Security Scanner & Contract Registry</p>

      <div style={{ display: 'flex', gap: '4px', marginBottom: '16px' }}>
        {['templates', 'scanner', 'registry'].map(t => (
          <button key={t} onClick={() => setTab(t)} style={{ ...btn, background: tab === t ? '#4F46E5' : '#1A1A1E', textTransform: 'capitalize' }}>{t}</button>
        ))}
      </div>

      {tab === 'templates' && (
        <div style={{ display: 'grid', gap: '8px' }}>
          {stats && (
            <div style={{ display: 'flex', gap: '8px' }}>
              <div style={{ ...panel, flex: 1, textAlign: 'center' }}>
                <div style={{ fontSize: '10px', color: '#888' }}>Templates</div>
                <div style={{ fontSize: '18px', fontWeight: 700 }}>{stats.total_templates}</div>
              </div>
              <div style={{ ...panel, flex: 1, textAlign: 'center' }}>
                <div style={{ fontSize: '10px', color: '#888' }}>Avg Security</div>
                <div style={{ fontSize: '18px', fontWeight: 700 }}>{stats.avg_security_score?.toFixed(1) || '—'}</div>
              </div>
              <div style={{ ...panel, flex: 1, textAlign: 'center' }}>
                <div style={{ fontSize: '10px', color: '#888' }}>Contracts</div>
                <div style={{ fontSize: '18px', fontWeight: 700 }}>{stats.total_contracts}</div>
              </div>
            </div>
          )}
          {templates.map((t, i) => (
            <div key={i} style={panel} onClick={() => setSelectedTemplate(selectedTemplate?.id === t.id ? null : t)}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <div style={{ fontSize: '13px', fontWeight: 600 }}>{t.name}</div>
                <span style={{ fontSize: '10px', padding: '2px 6px', borderRadius: '4px', background: '#4F46E522', color: '#4F46E5', textTransform: 'capitalize' }}>{t.category}</span>
              </div>
              <div style={{ fontSize: '11px', color: '#888', marginTop: '4px' }}>{t.description}</div>
              <div style={{ fontSize: '10px', color: '#666', marginTop: '4px' }}>{t.source_code.length} chars | {t.parameters?.length || 0} params</div>
              {selectedTemplate?.id === t.id && (
                <div style={{ marginTop: '8px' }}>
                  <div style={{ fontSize: '10px', color: '#888', marginBottom: '4px' }}>Source Code:</div>
                  <pre style={{ fontSize: '10px', color: '#888', background: '#0D0D0F', padding: '8px', borderRadius: '6px', overflow: 'auto', maxHeight: '300px' }}>{t.source_code}</pre>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {tab === 'scanner' && (
        <div style={{ display: 'grid', gap: '12px' }}>
          <div style={panel}>
            <div style={{ fontSize: '14px', fontWeight: 600, marginBottom: '8px' }}>Security Scanner</div>
            <textarea value={scanInput} onChange={e => setScanInput(e.target.value)} placeholder="Paste Solidity source code..." style={{ ...input, minHeight: '200px', fontFamily: 'monospace' }} />
            <button onClick={handleScan} style={{ ...btn, background: '#4F46E5', marginTop: '8px' }}>Scan Contract</button>
          </div>
          {scanResult && (
            <div style={panel}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <div style={{ fontSize: '14px', fontWeight: 600 }}>Scan Result: {scanResult.contract_name}</div>
                <div style={{ fontSize: '18px', fontWeight: 700, color: scanResult.score >= 80 ? '#22C55E' : scanResult.score >= 50 ? '#FFA500' : '#EF4444' }}>{scanResult.score.toFixed(1)}/100</div>
              </div>
              <div style={{ fontSize: '11px', color: '#888', marginTop: '4px' }}>{scanResult.lines_scanned} lines | {scanResult.checks_run} checks | {scanResult.vulnerabilities.length} findings</div>
              {scanResult.vulnerabilities.map((v, i) => (
                <div key={i} style={{ marginTop: '8px', padding: '8px', background: '#0D0D0F', borderRadius: '6px' }}>
                  <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                    <span style={{ fontSize: '10px', padding: '2px 6px', borderRadius: '4px', background: (sevColor[v.severity] || '#888') + '22', color: sevColor[v.severity] || '#888', fontWeight: 600, textTransform: 'uppercase' }}>{v.severity}</span>
                    <span style={{ fontSize: '12px', fontWeight: 600 }}>{v.title}</span>
                    <span style={{ fontSize: '10px', color: '#666' }}>L{v.line_number}</span>
                  </div>
                  <div style={{ fontSize: '11px', color: '#888', marginTop: '4px' }}>{v.description}</div>
                  <div style={{ fontSize: '10px', color: '#4F46E5', marginTop: '2px' }}>→ {v.recommendation}</div>
                </div>
              ))}
              {scanResult.vulnerabilities.length === 0 && <div style={{ fontSize: '12px', color: '#22C55E', marginTop: '8px' }}>✅ No vulnerabilities found!</div>}
            </div>
          )}
          {scans.length > 0 && (
            <div>
              <div style={{ fontSize: '12px', fontWeight: 600, marginBottom: '8px', color: '#888' }}>Recent Scans</div>
              {scans.slice(0, 5).map((s, i) => (
                <div key={i} style={{ ...panel, marginBottom: '4px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <div style={{ fontSize: '11px' }}>{s.contract_name}</div>
                    <span style={{ fontSize: '12px', fontWeight: 700, color: s.score >= 80 ? '#22C55E' : s.score >= 50 ? '#FFA500' : '#EF4444' }}>{s.score.toFixed(1)}</span>
                  </div>
                  <div style={{ fontSize: '10px', color: '#666' }}>{s.vulnerabilities.length} findings</div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {tab === 'registry' && (
        <div style={{ display: 'grid', gap: '8px' }}>
          {contracts.length === 0 && <div style={{ fontSize: '12px', color: '#888' }}>No contracts registered yet</div>}
          {contracts.map((c, i) => (
            <div key={i} style={panel}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <div style={{ fontSize: '13px', fontWeight: 600 }}>{c.name}</div>
                <span style={{ fontSize: '10px', padding: '2px 6px', borderRadius: '4px', background: c.verified ? '#22C55E22' : '#FFA50022', color: c.verified ? '#22C55E' : '#FFA500' }}>{c.verified ? '✓ Verified' : 'Unverified'}</span>
              </div>
              <div style={{ fontSize: '11px', color: '#4F46E5', fontFamily: 'monospace' }}>{c.address}</div>
              <div style={{ fontSize: '10px', color: '#888', marginTop: '4px' }}>{c.category} | {c.compiler_version} | {c.network}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default SmartContracts;
