import { useEffect, useRef, useState, useCallback } from 'react';

export default function useWebSocket(onMessage) {
  const [connected, setConnected] = useState(false);
  const wsRef = useRef(null);
  const reconnectTimer = useRef(null);

  const connect = useCallback(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const ws = new WebSocket(`${protocol}//${host}/ws`);

    ws.onopen = () => {
      setConnected(true);
      // Heartbeat
      wsRef.current._pingInterval = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) ws.send('ping');
      }, 30000);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type !== 'pong' && onMessage) {
          onMessage(data);
        }
      } catch (e) {
        // ignore non-JSON
      }
    };

    ws.onclose = () => {
      setConnected(false);
      if (wsRef.current?._pingInterval) clearInterval(wsRef.current._pingInterval);
      // Reconnect after 3 seconds
      reconnectTimer.current = setTimeout(connect, 3000);
    };

    ws.onerror = () => {
      ws.close();
    };

    wsRef.current = ws;
  }, [onMessage]);

  useEffect(() => {
    connect();
    return () => {
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      if (wsRef.current?._pingInterval) clearInterval(wsRef.current._pingInterval);
      if (wsRef.current) wsRef.current.close();
    };
  }, [connect]);

  return { connected };
}
