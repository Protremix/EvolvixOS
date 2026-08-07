import React, { useState, useEffect, useCallback } from 'react';
import { ethers } from 'ethers';

function WebWallet() {
  const [account, setAccount] = useState(null);
  const [balance, setBalance] = useState(null);
  const [chainHealth, setChainHealth] = useState(null);
  const [tab, setTab] = useState('wallet');
  const [sendTo, setSendTo] = useState('');
  const [sendAmount, setSendAmount] = useState('');
  const [txHistory, setTxHistory] = useState([]);
  const [evmContracts, setEvmContracts] = useState([]);
  const [ecoStats, setEcoStats] = useState(null);

  const RPC_URL = 'https://verdischain.com/rpc';
  const CHAIN_ID = 909;

  const connectWallet = useCallback(async () => {
    try {
      if (window.ethereum) {
        const provider = new ethers.BrowserProvider(window.ethereum);
        await window.ethereum.request({ method: 'eth_requestAccounts' });
        const signer = await provider.getSigner();
        const address = await signer.getAddress();
        setAccount(address);
        const bal = await provider.getBalance(address);
        setBalance(ethers.formatEther(bal));
      } else {
        // Generate a local wallet
        const wallet = ethers.Wallet.createRandom();
        setAccount(wallet.address);
        setBalance('1000.0 (test)');
      }
    } catch (err) { console.error(err); }
  }, []);

  const checkChainHealth = useCallback(async () => {
    try {
      const response = await fetch(RPC_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ jsonrpc: '2.0', method: 'system_health', id: 1 }),
      });
      const data = await response.json();
      setChainHealth(data.result);
    } catch (err) { console.error(err); }
  }, []);

  useEffect(() => {
    checkChainHealth();
    setEvmContracts([
      { name: 'VerdisToken (VRDX)', address: '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1' },
      { name: 'CarbonCredit', address: '0x55d35Cc6634C0532925a3b844Bc9e7595f0bEb2' },
    ]);
    setEcoStats({ totalIssued: 45000, totalRetired: 12000, net: 33000, validators: 14, avgScore: 847 });
    setTxHistory([
      { hash: '0x1a2b...', type: 'Send', amount: '50 VRDX', time: '2h ago', status: 'confirmed' },
      { hash: '0x3c4d...', type: 'Receive', amount: '100 VRDX', time: '5h ago', status: 'confirmed' },
      { hash: '0x5e6f...', type: 'Stake', amount: '500 VRDX', time: '1d ago', status: 'confirmed' },
    ]);
  }, []);

  const handleSend = async () => {
    if (!sendTo || !sendAmount) return;
    // Simulated send
    setTxHistory([{
      hash: '0x' + Math.random().toString(16).slice(2, 8) + '...',
      type: 'Send', amount: `${sendAmount} VRDX`, time: 'just now', status: 'pending'
    }, ...txHistory]);
    setSendTo(''); setSendAmount('');
  };

  const panel = { background: '#1A1A1E', borderRadius: '10px', border: '1px solid #333', padding: '14px' };
  const btn = { padding: '8px 16px', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '13px', color: '#fff' };
  const input = { padding: '8px 12px', background: '#0D0D0F', border: '1px solid #333', borderRadius: '6px', color: '#fff', fontSize: '13px' };

  return (
    <div style={{ padding: '24px', maxWidth: '600px', margin: '0 auto' }}>
      <h1 style={{ fontSize: '28px', fontWeight: 700, marginBottom: '4px' }}>👛 Verdis Wallet</h1>
      <p style={{ color: '#888', marginBottom: '20px' }}>Chain ID 909 · VRDX</p>

      {/* Account Card */}
      <div style={{ ...panel, marginBottom: '12px' }}>
        {account ? (
          <>
            <div style={{ fontSize: '11px', color: '#888' }}>Connected Address</div>
            <div style={{ fontSize: '13px', fontFamily: 'monospace', color: '#4F46E5', marginTop: '2px' }}>{account.slice(0, 10)}...{account.slice(-8)}</div>
            <div style={{ fontSize: '24px', fontWeight: 700, marginTop: '8px' }}>{balance} <span style={{ fontSize: '14px', color: '#888' }}>VRDX</span></div>
          </>
        ) : (
          <button onClick={connectWallet} style={{ ...btn, background: '#4F46E5', width: '100%' }}>Connect Wallet</button>
        )}
      </div>

      {/* Chain Health */}
      {chainHealth && (
        <div style={{ display: 'flex', gap: '8px', marginBottom: '12px' }}>
          <div style={{ ...panel, flex: 1, textAlign: 'center' }}>
            <div style={{ fontSize: '10px', color: '#888' }}>Peers</div>
            <div style={{ fontSize: '16px', fontWeight: 600, color: '#22C55E' }}>{chainHealth.peers || '?'}</div>
          </div>
          <div style={{ ...panel, flex: 1, textAlign: 'center' }}>
            <div style={{ fontSize: '10px', color: '#888' }}>Status</div>
            <div style={{ fontSize: '14px', fontWeight: 600, color: '#22C55E' }}>{chainHealth.isSyncing ? 'Syncing' : 'Synced'}</div>
          </div>
          <div style={{ ...panel, flex: 1, textAlign: 'center' }}>
            <div style={{ fontSize: '10px', color: '#888' }}>Should Sync</div>
            <div style={{ fontSize: '14px', fontWeight: 600, color: chainHealth.shouldHavePeers ? '#22C55E' : '#888' }}>{chainHealth.shouldHavePeers ? 'Yes' : 'No'}</div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '4px', marginBottom: '12px' }}>
        {['wallet', 'send', 'evm', 'eco'].map(t => (
          <button key={t} onClick={() => setTab(t)} style={{ ...btn, background: tab === t ? '#4F46E5' : '#1A1A1E', flex: 1, textTransform: 'capitalize' }}>{t}</button>
        ))}
      </div>

      {tab === 'wallet' && (
        <div style={{ display: 'grid', gap: '6px' }}>
          {txHistory.map((tx, i) => (
            <div key={i} style={{ ...panel, display: 'flex', justifyContent: 'space-between' }}>
              <div>
                <div style={{ fontSize: '13px', fontWeight: 600 }}>{tx.type}</div>
                <div style={{ fontSize: '10px', color: '#888', fontFamily: 'monospace' }}>{tx.hash}</div>
                <div style={{ fontSize: '10px', color: '#666' }}>{tx.time}</div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: '13px', fontWeight: 600, color: tx.type === 'Receive' ? '#22C55E' : '#fff' }}>{tx.amount}</div>
                <div style={{ fontSize: '10px', color: tx.status === 'confirmed' ? '#22C55E' : '#FFA500' }}>{tx.status}</div>
              </div>
            </div>
          ))}
        </div>
      )}

      {tab === 'send' && (
        <div style={{ ...panel }}>
          <input value={sendTo} onChange={e => setSendTo(e.target.value)} placeholder="Recipient address (0x...)" style={{ ...input, width: 'calc(100% - 26px)', marginBottom: '8px' }} />
          <input value={sendAmount} onChange={e => setSendAmount(e.target.value)} placeholder="Amount (VRDX)" type="number" style={{ ...input, width: 'calc(100% - 26px)', marginBottom: '12px' }} />
          <button onClick={handleSend} style={{ ...btn, background: '#4F46E5', width: '100%' }}>Send VRDX</button>
          <div style={{ fontSize: '10px', color: '#888', marginTop: '8px' }}>Gas: ~0.000021 VRDX (1 Gwei)</div>
        </div>
      )}

      {tab === 'evm' && (
        <div style={{ display: 'grid', gap: '6px' }}>
          <div style={{ fontSize: '12px', color: '#888', marginBottom: '4px' }}>Deployed Contracts</div>
          {evmContracts.map((c, i) => (
            <div key={i} style={{ ...panel }}>
              <div style={{ fontSize: '13px', fontWeight: 600 }}>{c.name}</div>
              <div style={{ fontSize: '10px', color: '#888', fontFamily: 'monospace', marginTop: '2px' }}>{c.address}</div>
            </div>
          ))}
          <div style={{ fontSize: '12px', color: '#888', marginTop: '8px', marginBottom: '4px' }}>Templates</div>
          {['ERC-20 Token', 'Carbon Credit', 'Green Validator'].map(t => (
            <div key={t} style={{ ...panel, display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ fontSize: '13px' }}>{t}</span>
              <button style={{ ...btn, background: '#4F46E5', padding: '4px 12px' }}>Deploy</button>
            </div>
          ))}
        </div>
      )}

      {tab === 'eco' && ecoStats && (
        <div style={{ display: 'grid', gap: '8px' }}>
          <div style={{ display: 'flex', gap: '8px' }}>
            <div style={{ ...panel, flex: 1, textAlign: 'center' }}>
              <div style={{ fontSize: '10px', color: '#888' }}>Carbon Issued</div>
              <div style={{ fontSize: '18px', fontWeight: 700, color: '#22C55E' }}>{(ecoStats.totalIssued / 1000).toFixed(0)}K</div>
              <div style={{ fontSize: '9px', color: '#666' }}>tons CO₂</div>
            </div>
            <div style={{ ...panel, flex: 1, textAlign: 'center' }}>
              <div style={{ fontSize: '10px', color: '#888' }}>Retired</div>
              <div style={{ fontSize: '18px', fontWeight: 700, color: '#4F46E5' }}>{(ecoStats.totalRetired / 1000).toFixed(0)}K</div>
              <div style={{ fontSize: '9px', color: '#666' }}>tons CO₂</div>
            </div>
            <div style={{ ...panel, flex: 1, textAlign: 'center' }}>
              <div style={{ fontSize: '10px', color: '#888' }}>Net Offset</div>
              <div style={{ fontSize: '18px', fontWeight: 700, color: '#22C55E' }}>{(ecoStats.net / 1000).toFixed(0)}K</div>
              <div style={{ fontSize: '9px', color: '#666' }}>tons CO₂</div>
            </div>
          </div>
          <div style={{ ...panel }}>
            <div style={{ fontSize: '13px', fontWeight: 600, marginBottom: '8px' }}>🌱 Green Validators</div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ fontSize: '12px', color: '#888' }}>Active Validators</span>
              <span style={{ fontSize: '12px', fontWeight: 600 }}>{ecoStats.validators}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ fontSize: '12px', color: '#888' }}>Avg Green Score</span>
              <span style={{ fontSize: '12px', fontWeight: 600, color: '#22C55E' }}>{ecoStats.avgScore}/1000</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default WebWallet;
