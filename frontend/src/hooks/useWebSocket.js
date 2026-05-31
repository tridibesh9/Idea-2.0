import { useEffect, useRef, useState, useCallback } from 'react';

export default function useWebSocket(onMessage) {
  const [connected, setConnected] = useState(false);
  const wsRef = useRef(null);
  const reconnectTimer = useRef(null);
  const onMessageRef = useRef(onMessage);

  // Keep callback reference updated
  useEffect(() => {
    onMessageRef.current = onMessage;
  }, [onMessage]);

  const connect = useCallback(() => {
    const viteApiUrl = import.meta.env.VITE_API_URL;
    let wsUrl = '';
    if (viteApiUrl) {
      const wsProtocol = viteApiUrl.startsWith('https') ? 'wss:' : 'ws:';
      const parsedHost = viteApiUrl.replace(/^https?:\/\//, '');
      wsUrl = `${wsProtocol}//${parsedHost}/ws`;
    } else {
      const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      wsUrl = `${wsProtocol}//${window.location.host}/ws`;
    }
    const ws = new WebSocket(wsUrl);

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
        if (data.type !== 'pong' && onMessageRef.current) {
          onMessageRef.current(data);
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
  }, []); // Connect has no changing dependencies now!

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
