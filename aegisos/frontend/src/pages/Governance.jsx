import React, { useState, useEffect, useCallback } from 'react';
import governanceService from '../services/governanceService';

function Governance() {
  const [tab, setTab] = useState('proposals');
  const [dashboard, setDashboard] = useState(null);
  const [proposals, setProposals] = useState([]);
  const [treasury, setTreasury] = useState([]);
  const [council, setCouncil] = useState([]);
  const [propForm, setPropForm] = useState({ type: 'referendum', title: '', description: '', proposer: '', threshold: 0.5, voting_period_days: 7 });
  const [trForm, setTrForm] = useState({ title: '', description: '', proposer: '', beneficiary: '', amount: 0, category: 'general', threshold: 3 });

  const fetchData = useCallback(async () => {
    try {
      const [dash, props, tr, cou] = await Promise.all([
        governanceService.dashboard(),
        governanceService.listProposals({}),
        governanceService.listTreasury({}),
        governanceService.listCouncil(true),
      ]);
      setDashboard(dash.data || null);
      setProposals(props.data || []);
      setTreasury(tr.data || []);
      setCouncil(cou.data || []);
    } catch (err) { console.error(err); }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleCreateProp = async () => {
    try { await governanceService.createProposal(propForm); setPropForm({ ...propForm, title: '', description: '' }); fetchData(); } catch (e) { console.error(e); }
  };
  const handleCreateTr = async () => {
    try { await governanceService.createTreasury(trForm); setTrForm({ ...trForm, title: '', description: '', amount: 0 }); fetchData(); } catch (e) { console.error(e); }
  };

  const statusColor = { active: '#4F46E5', passed: '#22C55E', rejected: '#EF4444', executed: '#22C55E', cancelled: '#888', expired: '#FFA500', pending: '#FFA500', approved: '#22C55E', disbursed: '#22C55E' };
  const panel = { background: '#1A1A1E', borderRadius: '10px', border: '1px solid #333', padding: '14px' };
  const btn = { padding: '8px 16px', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '13px', color: '#fff' };
  const input = { padding: '8px 12px', background: '#0D0D0F', border: '1px solid #333', borderRadius: '6px', color: '#fff', fontSize: '13px', width: '100%' };

  return (
    <div style={{ padding: '24px' }}>
      <h1 style={{ fontSize: '28px', fontWeight: 700, marginBottom: '4px' }}>🏛️ Governance</h1>
      <p style={{ color: '#888', marginBottom: '20px' }}>Proposals, Voting, Treasury & Council</p>

      <div style={{ display: 'flex', gap: '4px', marginBottom: '16px' }}>
        {['proposals', 'create', 'treasury', 'council'].map(t => (
          <button key={t} onClick={() => setTab(t)} style={{ ...btn, background: tab === t ? '#4F46E5' : '#1A1A1E', textTransform: 'capitalize' }}>{t}</button>
        ))}
      </div>

      {dashboard && tab === 'proposals' && (
        <div style={{ display: 'grid', gap: '12px' }}>
          <div style={{ display: 'flex', gap: '8px' }}>
            {[{ l: 'Active', v: dashboard.proposals?.active }, { l: 'Passed', v: dashboard.proposals?.passed }, { l: 'Executed', v: dashboard.proposals?.executed }, { l: 'Treasury', v: dashboard.treasury?.balance?.toLocaleString() }].map(s => (
              <div key={s.l} style={{ ...panel, flex: 1, textAlign: 'center' }}>
                <div style={{ fontSize: '10px', color: '#888' }}>{s.l}</div>
                <div style={{ fontSize: '18px', fontWeight: 700 }}>{s.v || 0}</div>
              </div>
            ))}
          </div>
          {proposals.map((p, i) => (
            <div key={i} style={panel}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <div style={{ fontSize: '13px', fontWeight: 600 }}>{p.title}</div>
                <span style={{ fontSize: '10px', padding: '2px 8px', borderRadius: '4px', background: (statusColor[p.status] || '#888') + '22', color: statusColor[p.status] || '#888', fontWeight: 600 }}>{p.status}</span>
              </div>
              <div style={{ fontSize: '11px', color: '#888', marginTop: '4px' }}>{p.description}</div>
              <div style={{ display: 'flex', gap: '12px', fontSize: '10px', marginTop: '6px' }}>
                <span style={{ color: '#22C55E' }}>✓ {p.aye_votes}</span>
                <span style={{ color: '#EF4444' }}>✗ {p.nay_votes}</span>
                <span style={{ color: '#888' }}>○ {p.abstain_votes}</span>
                <span style={{ color: '#666' }}>{p.type}</span>
              </div>
            </div>
          ))}
          {proposals.length === 0 && <div style={{ fontSize: '12px', color: '#888' }}>No proposals yet</div>}
        </div>
      )}

      {tab === 'create' && (
        <div style={{ ...panel, maxWidth: '500px' }}>
          <div style={{ fontSize: '14px', fontWeight: 600, marginBottom: '12px' }}>Create Proposal</div>
          <div style={{ display: 'grid', gap: '8px' }}>
            <select value={propForm.type} onChange={e => setPropForm({ ...propForm, type: e.target.value })} style={input}>
              <option value="referendum">Referendum</option>
              <option value="treasury_spend">Treasury Spend</option>
              <option value="council_motion">Council Motion</option>
              <option value="runtime_upgrade">Runtime Upgrade</option>
              <option value="parameter_change">Parameter Change</option>
              <option value="emergency">Emergency</option>
            </select>
            <input value={propForm.title} onChange={e => setPropForm({ ...propForm, title: e.target.value })} placeholder="Title" style={input} />
            <textarea value={propForm.description} onChange={e => setPropForm({ ...propForm, description: e.target.value })} placeholder="Description" style={{ ...input, minHeight: '60px' }} />
            <input value={propForm.proposer} onChange={e => setPropForm({ ...propForm, proposer: e.target.value })} placeholder="Proposer address" style={input} />
            <div style={{ display: 'flex', gap: '8px' }}>
              <input type="number" step="0.1" value={propForm.threshold} onChange={e => setPropForm({ ...propForm, threshold: parseFloat(e.target.value) })} placeholder="Threshold" style={input} />
              <input type="number" value={propForm.voting_period_days} onChange={e => setPropForm({ ...propForm, voting_period_days: parseInt(e.target.value) })} placeholder="Days" style={input} />
            </div>
            <button onClick={handleCreateProp} style={{ ...btn, background: '#4F46E5' }}>Create</button>
          </div>
        </div>
      )}

      {tab === 'treasury' && (
        <div style={{ display: 'grid', gap: '12px' }}>
          {dashboard && (
            <div style={{ display: 'flex', gap: '8px' }}>
              {[{ l: 'Balance', v: dashboard.treasury?.balance?.toLocaleString() }, { l: 'Disbursed', v: dashboard.treasury?.disbursed?.toLocaleString() }, { l: 'Pending', v: dashboard.treasury?.pending?.toLocaleString() }].map(s => (
                <div key={s.l} style={{ ...panel, flex: 1, textAlign: 'center' }}>
                  <div style={{ fontSize: '10px', color: '#888' }}>{s.l} VRS</div>
                  <div style={{ fontSize: '16px', fontWeight: 700 }}>{s.v || 0}</div>
                </div>
              ))}
            </div>
          )}
          <div style={{ ...panel, maxWidth: '500px' }}>
            <div style={{ fontSize: '14px', fontWeight: 600, marginBottom: '12px' }}>Treasury Proposal</div>
            <div style={{ display: 'grid', gap: '8px' }}>
              <input value={trForm.title} onChange={e => setTrForm({ ...trForm, title: e.target.value })} placeholder="Title" style={input} />
              <input value={trForm.description} onChange={e => setTrForm({ ...trForm, description: e.target.value })} placeholder="Description" style={input} />
              <input value={trForm.proposer} onChange={e => setTrForm({ ...trForm, proposer: e.target.value })} placeholder="Proposer" style={input} />
              <input value={trForm.beneficiary} onChange={e => setTrForm({ ...trForm, beneficiary: e.target.value })} placeholder="Beneficiary" style={input} />
              <div style={{ display: 'flex', gap: '8px' }}>
                <input type="number" value={trForm.amount} onChange={e => setTrForm({ ...trForm, amount: parseFloat(e.target.value) })} placeholder="Amount VRS" style={input} />
                <select value={trForm.category} onChange={e => setTrForm({ ...trForm, category: e.target.value })} style={input}>
                  <option value="general">General</option><option value="eco">Eco</option><option value="infra">Infra</option><option value="dev">Dev</option><option value="marketing">Marketing</option>
                </select>
              </div>
              <button onClick={handleCreateTr} style={{ ...btn, background: '#22C55E' }}>Create</button>
            </div>
          </div>
          {treasury.map((t, i) => (
            <div key={i} style={panel}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <div style={{ fontSize: '13px', fontWeight: 600 }}>{t.title}</div>
                <span style={{ fontSize: '10px', padding: '2px 6px', borderRadius: '4px', background: (statusColor[t.status] || '#888') + '22', color: statusColor[t.status] || '#888' }}>{t.status}</span>
              </div>
              <div style={{ fontSize: '12px', color: '#4F46E5', marginTop: '4px' }}>{t.amount?.toLocaleString()} {t.currency} → {t.beneficiary?.substring(0, 15)}...</div>
              <div style={{ fontSize: '10px', color: '#888', marginTop: '2px' }}>{t.category} | Approvals: {t.approvals}/{t.threshold}</div>
            </div>
          ))}
        </div>
      )}

      {tab === 'council' && (
        <div style={{ display: 'grid', gap: '8px' }}>
          {dashboard && (
            <div style={{ display: 'flex', gap: '8px' }}>
              {[{ l: 'Members', v: dashboard.council?.active_members }, { l: 'Votes Cast', v: dashboard.council?.total_votes_cast }, { l: 'Proposals', v: dashboard.council?.total_proposals_created }].map(s => (
                <div key={s.l} style={{ ...panel, flex: 1, textAlign: 'center' }}>
                  <div style={{ fontSize: '10px', color: '#888' }}>{s.l}</div>
                  <div style={{ fontSize: '18px', fontWeight: 700 }}>{s.v || 0}</div>
                </div>
              ))}
            </div>
          )}
          {council.map((m, i) => (
            <div key={i} style={panel}>
              <div style={{ fontSize: '13px', fontWeight: 600 }}>{m.name}</div>
              <div style={{ fontSize: '10px', fontFamily: 'monospace', color: '#4F46E5' }}>{m.address}</div>
              <div style={{ fontSize: '10px', color: '#888', marginTop: '4px' }}>Votes: {m.votes_cast} | Proposals: {m.proposals_created}</div>
            </div>
          ))}
          {council.length === 0 && <div style={{ fontSize: '12px', color: '#888' }}>No council members</div>}
        </div>
      )}
    </div>
  );
}

export default Governance;
