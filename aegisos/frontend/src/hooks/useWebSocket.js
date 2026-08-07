import { useEffect, useRef, useCallback, useState } from 'react';

/**
 * WebSocket hook for real-time EvolvixOS updates.
 * Connects to /api/v1/ws?token=<jwt> and receives push events.
 *
 * @param {string} token - JWT auth token
 * @returns {object} { connected, lastEvent, send, subscribe, reconnect }
 */
export const useWebSocket = (token) => {
  const [connected, setConnected] = useState(false);
  const [lastEvent, setLastEvent] = useState(null);
  const wsRef = useRef(null);
  const reconnectTimer = useRef(null);
  const listenersRef = useRef(new Set());

  const connect = useCallback(() => {
    if (!token) return;

    if (wsRef.current && wsRef.current.readyState !== WebSocket.CLOSED) {
      wsRef.current.close();
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/api/v1/ws?token=${token}`;

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
      console.log('[EvolvixOS WS] Connected');
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        setLastEvent(msg);
        listenersRef.current.forEach(listener => listener(msg));
      } catch (e) {
        console.error('[EvolvixOS WS] Parse error:', e);
      }
    };

    ws.onclose = () => {
      setConnected(false);
      reconnectTimer.current = setTimeout(() => {
        if (token) connect();
      }, 3000);
    };

    ws.onerror = () => {
      ws.close();
    };
  }, [token]);

  const send = useCallback((data) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    }
  }, []);

  const subscribe = useCallback((callback) => {
    listenersRef.current.add(callback);
    return () => listenersRef.current.delete(callback);
  }, []);

  const reconnect = useCallback(() => {
    connect();
  }, [connect]);

  useEffect(() => {
    connect();
    return () => {
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      if (wsRef.current) wsRef.current.close();
    };
  }, [connect]);

  useEffect(() => {
    if (!connected) return;
    const interval = setInterval(() => {
      send({ action: 'ping' });
    }, 30000);
    return () => clearInterval(interval);
  }, [connected, send]);

  return { connected, lastEvent, send, subscribe, reconnect };
};

export default useWebSocket;
