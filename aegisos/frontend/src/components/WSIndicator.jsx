import React from 'react';
import { Wifi, WifiOff } from 'lucide-react';
import { useAuthStore } from '../store/authStore';
import useWebSocket from '../hooks/useWebSocket';

const WSIndicator = () => {
  const { token } = useAuthStore();
  const { connected } = useWebSocket(token);

  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: '0.375rem',
      padding: '0.375rem 0.75rem', borderRadius: '9999px',
      backgroundColor: connected ? 'rgba(0,255,136,0.08)' : 'rgba(239,68,68,0.08)',
      border: connected ? '1px solid rgba(0,255,136,0.2)' : '1px solid rgba(239,68,68,0.2)',
      fontSize: '0.6875rem', fontWeight: '600',
      color: connected ? '#00ff88' : '#ef4444',
    }}>
      {connected ? <Wifi size={12} /> : <WifiOff size={12} />}
      <span>{connected ? 'Live' : 'Offline'}</span>
      <span style={{
        width: 5, height: 5, borderRadius: '50%',
        backgroundColor: 'currentColor',
        boxShadow: connected ? '0 0 4px #00ff88' : 'none',
      }} />
    </div>
  );
};

export default WSIndicator;
