import React, { useState, useEffect, useCallback } from 'react';
import securityService from '../services/securityService';

function Security() {
  const [tab, setTab] = useState('2fa');
  const [twoFAStatus, setTwoFAStatus] = useState(null);
  const [twoFASetup, setTwoFASetup] = useState(null);
  const [verifyCode, setVerifyCode] = useState('');
  const [scanSummary, setScanSummary] = useState(null);
  const [scanResults, setScanResults] = useState([]);
  const [txStats, setTxStats] = useState(null);

  const fetchAll = useCallback(async () => {
    try {
      const [status, summary, stats] = await Promise.all([
        securityService.status2FA(),
        securityService.scanSummary(),
        securityService.txStats(),
      ]);
      setTwoFAStatus(status.data);
      setScanSummary(summary.data);
      setTxStats(stats.data);
    } catch (err) { console.error(err); }
  }, []);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  const handleSetup2FA = async () => {
    try {
      const resp = await securityService.setup2FA();
      setTwoFASetup(resp.data);
    } catch (err) { console.error(err); }
  };

  const handleEnable2FA = async () => {
    try {
      await securityService.enable2FA({
        secret: twoFASetup.secret,
        verification_code: verifyCode,
      });
      setTwoFASetup(null);
      setVerifyCode('');
      fetchAll();
    } catch (err) { console.error(err); }
  };

  const handleScan = async () => {
    try {
      const resp = await securityService.scan();
      setScanResults(resp.data.results || []);
      fetchAll();
    } catch (err) { console.error(err); }
  };

  const panel = { background: '#1A1A1E', borderRadius: '10px', border: '1px solid #333', padding: '14px' };
  const btn = { padding: '8px 16px', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '13px', color: '#fff' };
  const input = { padding: '8px 12px', background: '#0D0D0F', border: '1px solid #333', borderRadius: '6px', color: '#fff', fontSize: '13px' };
  const sevColor = { high: '#EF4444', medium: '#FFA500', low: '#22C55E' };

  return (
    <div style={{ padding: '24px' }}>
      <h1 style={{ fontSize: '28px', fontWeight: 700, marginBottom: '4px' }}>🔒 Security</h1>
      <p style={{ color: '#888', marginBottom: '20px' }}>Two-factor auth, transaction security, vulnerability scanning</p>

      <div style={{ display: 'flex', gap: '4px', marginBottom: '16px' }}>
        {['2fa', 'transactions', 'scanner'].map(t => (
          <button key={t} onClick={() => setTab(t)} style={{ ...btn, background: tab === t ? '#4F46E5' : '#1A1A1E', textTransform: 'capitalize' }}>{t === '2fa' ? '2FA' : t}</button>
        ))}
      </div>

      {tab === '2fa' && (
        <div style={{ display: 'grid', gap: '8px' }}>
          <div style={{ ...panel }}>
            <div style={{ fontSize: '14px', fontWeight: 600, marginBottom: '8px' }}>Two-Factor Authentication</div>
            {twoFAStatus?.enabled ? (
              <>
                <div style={{ fontSize: '13px', color: '#22C55E', marginBottom: '8px' }}>✅ 2FA is enabled</div>
                <button onClick={async () => { await securityService.disable2FA(); fetchAll(); }} style={{ ...btn, background: '#EF4444' }}>Disable 2FA</button>
              </>
            ) : twoFASetup ? (
              <>
                <div style={{ fontSize: '12px', color: '#888', marginBottom: '8px' }}>Scan this secret in your authenticator app:</div>
                <div style={{ fontSize: '11px', fontFamily: 'monospace', color: '#4F46E5', marginBottom: '4px' }}>{twoFASetup.secret}</div>
                <div style={{ fontSize: '10px', color: '#888', marginBottom: '12px' }}>{twoFASetup.otpauth_url}</div>
                <input value={verifyCode} onChange={e => setVerifyCode(e.target.value)} placeholder="Enter verification code" style={{ ...input, marginBottom: '8px' }} />
                <button onClick={handleEnable2FA} style={{ ...btn, background: '#22C55E' }}>Enable</button>
              </>
            ) : (
              <button onClick={handleSetup2FA} style={{ ...btn, background: '#4F46E5' }}>Set up 2FA</button>
            )}
          </div>
        </div>
      )}

      {tab === 'transactions' && txStats && (
        <div style={{ display: 'grid', gap: '8px' }}>
          <div style={{ display: 'flex', gap: '8px' }}>
            <div style={{ ...panel, flex: 1, textAlign: 'center' }}>
              <div style={{ fontSize: '10px', color: '#888' }}>Total Transactions</div>
              <div style={{ fontSize: '18px', fontWeight: 700 }}>{txStats.total_transactions}</div>
            </div>
            <div style={{ ...panel, flex: 1, textAlign: 'center' }}>
              <div style={{ fontSize: '10px', color: '#888' }}>Unique Senders</div>
              <div style={{ fontSize: '18px', fontWeight: 700 }}>{txStats.unique_senders}</div>
            </div>
            <div style={{ ...panel, flex: 1, textAlign: 'center' }}>
              <div style={{ fontSize: '10px', color: '#888' }}>Chain ID</div>
              <div style={{ fontSize: '18px', fontWeight: 700 }}>{txStats.chain_id}</div>
            </div>
          </div>
          <div style={{ ...panel }}>
            <div style={{ fontSize: '13px', fontWeight: 600, marginBottom: '8px' }}>Transaction Security</div>
            <div style={{ fontSize: '12px', color: '#888' }}>• SHA-256 payload hashing</div>
            <div style={{ fontSize: '12px', color: '#888' }}>• HMAC-SHA256 signing</div>
            <div style={{ fontSize: '12px', color: '#888' }}>• Nonce-based replay prevention</div>
            <div style={{ fontSize: '12px', color: '#888' }}>• Chain ID binding (909)</div>
            <div style={{ fontSize: '12px', color: '#888' }}>• Timestamp verification</div>
          </div>
        </div>
      )}

      {tab === 'scanner' && (
        <div style={{ display: 'grid', gap: '8px' }}>
          {scanSummary && (
            <div style={{ display: 'flex', gap: '8px' }}>
              <div style={{ ...panel, flex: 1, textAlign: 'center' }}>
                <div style={{ fontSize: '10px', color: '#888' }}>Total Findings</div>
                <div style={{ fontSize: '18px', fontWeight: 700, color: scanSummary.total_findings > 0 ? '#FFA500' : '#22C55E' }}>{scanSummary.total_findings}</div>
              </div>
              <div style={{ ...panel, flex: 1, textAlign: 'center' }}>
                <div style={{ fontSize: '10px', color: '#888' }}>High</div>
                <div style={{ fontSize: '18px', fontWeight: 700, color: '#EF4444' }}>{scanSummary.by_severity?.high || 0}</div>
              </div>
              <div style={{ ...panel, flex: 1, textAlign: 'center' }}>
                <div style={{ fontSize: '10px', color: '#888' }}>Medium</div>
                <div style={{ fontSize: '18px', fontWeight: 700, color: '#FFA500' }}>{scanSummary.by_severity?.medium || 0}</div>
              </div>
              <div style={{ ...panel, flex: 1, textAlign: 'center' }}>
                <div style={{ fontSize: '10px', color: '#888' }}>Low</div>
                <div style={{ fontSize: '18px', fontWeight: 700, color: '#22C55E' }}>{scanSummary.by_severity?.low || 0}</div>
              </div>
            </div>
          )}
          <button onClick={handleScan} style={{ ...btn, background: '#4F46E5' }}>Run Security Scan</button>
          {scanResults.length > 0 && (
            <div style={{ display: 'grid', gap: '4px' }}>
              {scanResults.map((f, i) => (
                <div key={i} style={{ ...panel }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ fontSize: '11px', padding: '2px 6px', borderRadius: '4px', background: (sevColor[f.severity] || '#888') + '22', color: sevColor[f.severity] || '#888', fontWeight: 600 }}>{f.severity}</span>
                    <span style={{ fontSize: '10px', color: '#888' }}>{f.pattern}</span>
                  </div>
                  <div style={{ fontSize: '12px', marginTop: '4px' }}>{f.description}</div>
                  <div style={{ fontSize: '10px', color: '#888', fontFamily: 'monospace', marginTop: '2px' }}>{f.file}:{f.line}</div>
                  <div style={{ fontSize: '10px', color: '#666', fontFamily: 'monospace', marginTop: '2px' }}>{f.code_snippet}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default Security;
