import React, { useState, useEffect, useCallback } from 'react';
import identityService from '../services/identityService';
import identityEnhancedService from '../services/identityEnhancedService';

function Identity() {
  const [tab, setTab] = useState('dids');
  const [dids, setDids] = useState([]);
  const [stats, setStats] = useState(null);
  const [credentials, setCredentials] = useState([]);
  const [schemas, setSchemas] = useState([]);
  const [presentations, setPresentations] = useState([]);
  const [sdkInfo, setSdkInfo] = useState(null);
  const [createForm, setCreateForm] = useState({ name: '', email: '', role: 'user' });
  const [issueForm, setIssueForm] = useState({ issuer_did: '', subject_did: '', credential_type: 'kyc', claims: '{"country": "Spain", "verified": true}', expiration_days: 365 });
  const [resolveInput, setResolveInput] = useState('');
  const [resolveResult, setResolveResult] = useState(null);

  const fetchAll = useCallback(async () => {
    try {
      const [didsResp, statsResp, credsResp, schemasResp, presResp, sdkResp] = await Promise.all([
        identityService.listDIDs(50, 0),
        identityService.stats(),
        identityService.listCredentials(null, 50),
        identityEnhancedService.listSchemas(),
        identityEnhancedService.listPresentations(null, 50),
        identityEnhancedService.sdkInfo(),
      ]);
      setDids(didsResp.data || []);
      setStats(statsResp.data || {});
      setCredentials(credsResp.data || []);
      setSchemas(schemasResp.data || []);
      setPresentations(presResp.data || []);
      setSdkInfo(sdkResp.data || null);
    } catch (err) { console.error(err); }
  }, []);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  const handleCreate = async () => {
    try { await identityService.createDID(createForm); setCreateForm({ name: '', email: '', role: 'user' }); fetchAll(); } catch (e) { console.error(e); }
  };
  const handleIssue = async () => {
    try { await identityService.issueCredential({ ...issueForm, claims: JSON.parse(issueForm.claims) }); fetchAll(); } catch (e) { console.error(e); }
  };
  const handleResolve = async () => {
    try { const r = await identityEnhancedService.resolveDID(resolveInput); setResolveResult(r.data); } catch (e) { console.error(e); }
  };

  const panel = { background: '#1A1A1E', borderRadius: '10px', border: '1px solid #333', padding: '14px' };
  const btn = { padding: '8px 16px', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '13px', color: '#fff' };
  const input = { padding: '8px 12px', background: '#0D0D0F', border: '1px solid #333', borderRadius: '6px', color: '#fff', fontSize: '13px', width: '100%' };

  return (
    <div style={{ padding: '24px' }}>
      <h1 style={{ fontSize: '28px', fontWeight: 700, marginBottom: '4px' }}>🆔 Identity</h1>
      <p style={{ color: '#888', marginBottom: '20px' }}>DIDs, Verifiable Credentials, Presentations & Schemas</p>

      <div style={{ display: 'flex', gap: '4px', marginBottom: '16px', flexWrap: 'wrap' }}>
        {['dids', 'create', 'credentials', 'issue', 'schemas', 'presentations', 'resolve', 'sdk'].map(t => (
          <button key={t} onClick={() => setTab(t)} style={{ ...btn, background: tab === t ? '#4F46E5' : '#1A1A1E', textTransform: 'capitalize' }}>{t}</button>
        ))}
      </div>

      {tab === 'dids' && (
        <div style={{ display: 'grid', gap: '8px' }}>
          {stats && (
            <div style={{ display: 'flex', gap: '8px' }}>
              {[{ l: 'DIDs', v: stats.total_dids }, { l: 'Verified', v: stats.verified_identities }, { l: 'Creds', v: stats.total_credentials }, { l: 'Revoked', v: stats.revoked_credentials }].map(s => (
                <div key={s.l} style={{ ...panel, flex: 1, textAlign: 'center' }}>
                  <div style={{ fontSize: '10px', color: '#888' }}>{s.l}</div>
                  <div style={{ fontSize: '18px', fontWeight: 700 }}>{s.v || 0}</div>
                </div>
              ))}
            </div>
          )}
          {dids.map((d, i) => (
            <div key={i} style={panel}>
              <div style={{ fontSize: '12px', fontFamily: 'monospace', color: '#4F46E5' }}>{d.id}</div>
              <div style={{ fontSize: '10px', color: '#888' }}>{d.verification_method?.length || 0} keys</div>
            </div>
          ))}
          {dids.length === 0 && <div style={{ fontSize: '12px', color: '#888' }}>No DIDs yet</div>}
        </div>
      )}

      {tab === 'create' && (
        <div style={{ ...panel, maxWidth: '400px' }}>
          <div style={{ fontSize: '14px', fontWeight: 600, marginBottom: '12px' }}>Create Identity</div>
          <div style={{ display: 'grid', gap: '8px' }}>
            <input value={createForm.name} onChange={e => setCreateForm({ ...createForm, name: e.target.value })} placeholder="Name" style={input} />
            <input value={createForm.email} onChange={e => setCreateForm({ ...createForm, email: e.target.value })} placeholder="Email" style={input} />
            <select value={createForm.role} onChange={e => setCreateForm({ ...createForm, role: e.target.value })} style={input}>
              <option value="user">User</option><option value="validator">Validator</option><option value="developer">Developer</option><option value="partner">Partner</option><option value="admin">Admin</option>
            </select>
            <button onClick={handleCreate} style={{ ...btn, background: '#4F46E5' }}>Create DID</button>
          </div>
        </div>
      )}

      {tab === 'credentials' && (
        <div style={{ display: 'grid', gap: '8px' }}>
          {credentials.map((c, i) => (
            <div key={i} style={panel}>
              <div style={{ fontSize: '11px', fontFamily: 'monospace', color: '#4F46E5' }}>{c.id}</div>
              <div style={{ fontSize: '11px', color: '#888' }}>{c.type?.filter(t => t !== 'VerifiableCredential').join(', ')}</div>
              <div style={{ fontSize: '10px', color: '#666' }}>{JSON.stringify(c.claims)}</div>
            </div>
          ))}
          {credentials.length === 0 && <div style={{ fontSize: '12px', color: '#888' }}>No credentials</div>}
        </div>
      )}

      {tab === 'issue' && (
        <div style={{ ...panel, maxWidth: '500px' }}>
          <div style={{ fontSize: '14px', fontWeight: 600, marginBottom: '12px' }}>Issue Credential</div>
          <div style={{ display: 'grid', gap: '8px' }}>
            <input value={issueForm.issuer_did} onChange={e => setIssueForm({ ...issueForm, issuer_did: e.target.value })} placeholder="Issuer DID" style={input} />
            <input value={issueForm.subject_did} onChange={e => setIssueForm({ ...issueForm, subject_did: e.target.value })} placeholder="Subject DID" style={input} />
            <select value={issueForm.credential_type} onChange={e => setIssueForm({ ...issueForm, credential_type: e.target.value })} style={input}>
              <option value="kyc">KYC</option><option value="green_validator">Green Validator</option><option value="carbon_credit">Carbon Credit</option><option value="reforestation">Reforestation</option><option value="developer">Developer</option><option value="ecosystem_partner">Ecosystem Partner</option>
            </select>
            <textarea value={issueForm.claims} onChange={e => setIssueForm({ ...issueForm, claims: e.target.value })} style={{ ...input, minHeight: '60px', fontFamily: 'monospace' }} />
            <button onClick={handleIssue} style={{ ...btn, background: '#22C55E' }}>Issue</button>
          </div>
        </div>
      )}

      {tab === 'schemas' && (
        <div style={{ display: 'grid', gap: '8px' }}>
          {schemas.map((s, i) => (
            <div key={i} style={panel}>
              <div style={{ fontSize: '13px', fontWeight: 600 }}>{s.name}</div>
              <div style={{ fontSize: '11px', color: '#888' }}>{s.description}</div>
              <div style={{ fontSize: '10px', color: '#4F46E5', marginTop: '4px' }}>Required: {s.required_fields?.join(', ')}</div>
              {s.optional_fields?.length > 0 && <div style={{ fontSize: '10px', color: '#666' }}>Optional: {s.optional_fields.join(', ')}</div>}
            </div>
          ))}
        </div>
      )}

      {tab === 'presentations' && (
        <div style={{ display: 'grid', gap: '8px' }}>
          {presentations.map((p, i) => (
            <div key={i} style={panel}>
              <div style={{ fontSize: '11px', fontFamily: 'monospace', color: '#4F46E5' }}>{p.id}</div>
              <div style={{ fontSize: '11px', color: '#888' }}>{p.credentials?.length || 0} credentials</div>
              <div style={{ fontSize: '10px', color: '#666' }}>Holder: {p.holder?.substring(0, 25)}...</div>
            </div>
          ))}
          {presentations.length === 0 && <div style={{ fontSize: '12px', color: '#888' }}>No presentations</div>}
        </div>
      )}

      {tab === 'resolve' && (
        <div style={{ ...panel, maxWidth: '500px' }}>
          <div style={{ fontSize: '14px', fontWeight: 600, marginBottom: '12px' }}>DID Resolution</div>
          <div style={{ display: 'flex', gap: '8px' }}>
            <input value={resolveInput} onChange={e => setResolveInput(e.target.value)} placeholder="did:verdis:..." style={input} />
            <button onClick={handleResolve} style={{ ...btn, background: '#4F46E5', whiteSpace: 'nowrap' }}>Resolve</button>
          </div>
          {resolveResult && (
            <div style={{ marginTop: '12px', padding: '8px', background: '#0D0D0F', borderRadius: '6px' }}>
              <div style={{ fontSize: '11px', color: resolveResult.resolved ? '#22C55E' : '#EF4444' }}>
                {resolveResult.resolved ? '✅ Resolved' : '❌ ' + resolveResult.error}
              </div>
              {resolveResult.did_document && (
                <pre style={{ fontSize: '10px', color: '#888', overflow: 'auto', marginTop: '4px' }}>
                  {JSON.stringify(resolveResult.did_document, null, 2)}
                </pre>
              )}
              {resolveResult.profile && (
                <div style={{ fontSize: '11px', color: '#888', marginTop: '4px' }}>
                  Name: {resolveResult.profile.name} | Role: {resolveResult.profile.role} | Verified: {resolveResult.profile.verified?.toString()}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {tab === 'sdk' && sdkInfo && (
        <div style={panel}>
          <div style={{ fontSize: '14px', fontWeight: 600, marginBottom: '8px' }}>Developer SDK</div>
          <div style={{ fontSize: '12px', color: '#888' }}>Version: {sdkInfo.version} | DID Method: {sdkInfo.did_method}</div>
          <div style={{ fontSize: '11px', color: '#4F46E5', marginTop: '8px' }}>Credential Types: {sdkInfo.credential_types?.join(', ')}</div>
          <div style={{ fontSize: '11px', color: '#888', marginTop: '8px' }}>Endpoints:</div>
          <div style={{ fontSize: '10px', color: '#666', fontFamily: 'monospace', marginTop: '4px' }}>
            {Object.entries(sdkInfo.endpoints || {}).map(([k, v]) => (
              <div key={k}>{k}: {v}</div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default Identity;
