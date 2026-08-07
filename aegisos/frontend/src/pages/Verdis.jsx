import React from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Link as LinkIcon, Boxes, Users, Wifi, Activity,
  CheckCircle, AlertCircle, Cpu, Hash, Layers, Network
} from 'lucide-react';
import verdisService from '../services/verdisService';

const Verdis = () => {
  const { data: health, isLoading: healthLoading } = useQuery({
    queryKey: ['verdis-health'],
    queryFn: verdisService.getHealth,
    refetchInterval: 15000,
    retry: 1,
  });

  const { data: network } = useQuery({
    queryKey: ['verdis-network'],
    queryFn: verdisService.getNetwork,
    refetchInterval: 30000,
    retry: 1,
  });

  const { data: validatorsData } = useQuery({
    queryKey: ['verdis-validators'],
    queryFn: verdisService.getValidators,
    refetchInterval: 30000,
    retry: 1,
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div>
        <h1 style={{ fontSize: '1.75rem', fontWeight: '800', color: '#f0fdf4' }}>
          Verdis Blockchain
        </h1>
        <p style={{ color: '#8e9b8e', marginTop: '0.25rem', fontSize: '0.875rem' }}>
          Live monitoring of the Verdis Layer-1 blockchain (first EvolvixOS managed project)
        </p>
      </div>

      {/* Health Status Bar */}
      <div style={{
        backgroundColor: '#121812', border: '1px solid #1f2e1f', borderRadius: '12px',
        padding: '1.25rem', display: 'flex', alignItems: 'center', gap: '1rem',
      }}>
        <div style={{
          width: 48, height: 48, borderRadius: 12,
          background: health?.connected ? 'rgba(0,255,136,0.15)' : 'rgba(239,68,68,0.15)',
          border: health?.connected ? '1px solid rgba(0,255,136,0.3)' : '1px solid rgba(239,68,68,0.3)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          {health?.connected ? <CheckCircle size={24} color="#00ff88" /> : <AlertCircle size={24} color="#ef4444" />}
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: '1.1rem', fontWeight: '700', color: health?.connected ? '#00ff88' : '#ef4444' }}>
            {healthLoading ? 'Connecting...' : health?.connected ? 'Blockchain Connected' : 'Disconnected'}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#8e9b8e' }}>
            {health?.token_symbol && `Token: ${health.token_symbol}`}
            {health?.spec_version && ` · Spec v${health.spec_version}`}
          </div>
        </div>
        <div style={{
          display: 'inline-flex', alignItems: 'center', gap: '0.375rem',
          padding: '0.375rem 0.75rem', borderRadius: '9999px',
          backgroundColor: health?.is_syncing ? 'rgba(245,158,11,0.12)' : 'rgba(0,255,136,0.12)',
          border: health?.is_syncing ? '1px solid rgba(245,158,11,0.25)' : '1px solid rgba(0,255,136,0.25)',
          fontSize: '0.75rem', fontWeight: '600', color: health?.is_syncing ? '#f59e0b' : '#00ff88',
        }}>
          <Activity size={12} />
          {health?.is_syncing ? 'Syncing' : 'Synced'}
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid-4">
        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <span style={{ fontSize: '0.875rem', color: '#8e9b8e' }}>Block Height</span>
            <Hash size={18} color="#3b82f6" />
          </div>
          <div style={{ fontSize: '1.5rem', fontWeight: '800', color: '#f0fdf4', fontFamily: 'monospace' }}>
            {health?.block_height ? parseInt(health.block_height, 16) || health.block_height : '—'}
          </div>
        </div>

        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <span style={{ fontSize: '0.875rem', color: '#8e9b8e' }}>Peers</span>
            <Wifi size={18} color="#06b6d4" />
          </div>
          <div style={{ fontSize: '1.5rem', fontWeight: '800', color: '#f0fdf4' }}>
            {health?.peers ?? '—'}
          </div>
        </div>

        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <span style={{ fontSize: '0.875rem', color: '#8e9b8e' }}>Validators</span>
            <Users size={18} color="#a855f7" />
          </div>
          <div style={{ fontSize: '1.5rem', fontWeight: '800', color: '#f0fdf4' }}>
            {health?.active_validators ?? '—'}
          </div>
        </div>

        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <span style={{ fontSize: '0.875rem', color: '#8e9b8e' }}>RPC Methods</span>
            <Layers size={18} color="#00ff88" />
          </div>
          <div style={{ fontSize: '1.5rem', fontWeight: '800', color: '#f0fdf4' }}>
            {network?.rpc_method_count ?? '—'}
          </div>
        </div>
      </div>

      {/* Network Info & Validators */}
      <div className="grid-2">
        {/* Network Info */}
        <div className="card">
          <h2 style={{ fontSize: '1.1rem', fontWeight: '700', color: '#f0fdf4', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Network size={20} color="#3b82f6" />
            Network Info
          </h2>
          {network ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.625rem' }}>
              {[
                ['Chain', network.chain],
                ['Node', network.node_name],
                ['Version', network.node_version],
                ['Consensus', network.consensus],
                ['RPC URL', network.rpc_url || 'https://verdischain.com/rpc'],
              ].map(([label, value]) => (
                <div key={label} style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem 0', borderBottom: '1px solid #1f2e1f' }}>
                  <span style={{ fontSize: '0.8125rem', color: '#8e9b8e' }}>{label}</span>
                  <span style={{ fontSize: '0.8125rem', color: '#f0fdf4', fontWeight: '500' }}>{value || '—'}</span>
                </div>
              ))}
            </div>
          ) : (
            <p style={{ color: '#526352', fontSize: '0.875rem' }}>Loading network info...</p>
          )}
        </div>

        {/* Validators */}
        <div className="card">
          <h2 style={{ fontSize: '1.1rem', fontWeight: '700', color: '#f0fdf4', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Boxes size={20} color="#a855f7" />
            Active Validators
          </h2>
          {validatorsData?.validators?.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.375rem' }}>
              {validatorsData.validators.map((v, i) => (
                <div key={i} style={{
                  display: 'flex', alignItems: 'center', gap: '0.5rem',
                  padding: '0.5rem 0.75rem', backgroundColor: '#0e140e',
                  border: '1px solid #1f2e1f', borderRadius: '8px',
                }}>
                  <span style={{
                    width: 8, height: 8, borderRadius: '50%',
                    backgroundColor: '#00ff88', boxShadow: '0 0 4px #00ff88',
                  }} />
                  <span style={{ fontSize: '0.75rem', color: '#f0fdf4', fontFamily: 'monospace' }}>
                    {v.address}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p style={{ color: '#526352', fontSize: '0.875rem' }}>No validators data available.</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default Verdis;
