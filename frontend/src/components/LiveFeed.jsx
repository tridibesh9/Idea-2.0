import { useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { Radio, AlertTriangle, MessageSquare, RefreshCw } from 'lucide-react';
import useWebSocket from '../hooks/useWebSocket';
import { useToast } from './Toast';

const EVENT_ICONS = {
  new_complaint: MessageSquare,
  sla_breach: AlertTriangle,
  status_change: RefreshCw,
};

const EVENT_COLORS = {
  new_complaint: 'text-blue-500',
  sla_breach: 'text-red-500',
  status_change: 'text-yellow-500',
};

export default function LiveFeed() {
  const [events, setEvents] = useState([]);
  const addToast = useToast();

  const handleMessage = useCallback((data) => {
    const event = {
      ...data,
      id: Date.now() + Math.random(),
      timestamp: new Date(),
    };
    setEvents((prev) => [event, ...prev].slice(0, 20));

    // Show toast notification
    if (data.type === 'new_complaint') {
      addToast(
        `New ${data.severity || ''} complaint via ${data.channel}: ${data.subject?.slice(0, 50) || 'No subject'}`,
        data.severity === 'critical' ? 'error' : 'info'
      );
    } else if (data.type === 'sla_breach') {
      addToast(
        `SLA Breached: ${data.subject?.slice(0, 50) || data.complaint_id?.slice(0, 8)}`,
        'warning'
      );
    } else if (data.type === 'status_change') {
      addToast(
        `Status updated to "${data.status}" — ${data.subject?.slice(0, 40) || ''}`,
        'success'
      );
    }
  }, [addToast]);

  const { connected } = useWebSocket(handleMessage);

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border dark:border-gray-700 p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold text-gray-800 dark:text-gray-200 flex items-center gap-2">
          <Radio size={16} className={connected ? 'text-green-500 animate-pulse' : 'text-gray-400'} />
          Live Feed
        </h3>
        <span className={`text-xs px-2 py-0.5 rounded-full ${connected ? 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-400' : 'bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-400'}`}>
          {connected ? 'Connected' : 'Reconnecting...'}
        </span>
      </div>

      <div className="space-y-2 max-h-64 overflow-y-auto">
        {events.length === 0 ? (
          <p className="text-sm text-gray-400 dark:text-gray-500 text-center py-4">
            Waiting for real-time events...
          </p>
        ) : (
          events.map((evt) => {
            const Icon = EVENT_ICONS[evt.type] || MessageSquare;
            const color = EVENT_COLORS[evt.type] || 'text-gray-500';
            return (
              <div key={evt.id} className="flex items-start gap-2 p-2 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700/50 text-sm">
                <Icon size={14} className={`mt-0.5 flex-shrink-0 ${color}`} />
                <div className="flex-1 min-w-0">
                  <p className="text-gray-700 dark:text-gray-300 truncate">
                    {evt.type === 'new_complaint' && `New complaint via ${evt.channel}`}
                    {evt.type === 'sla_breach' && `SLA breached`}
                    {evt.type === 'status_change' && `Status → ${evt.status}`}
                    {evt.subject && `: ${evt.subject.slice(0, 50)}`}
                  </p>
                  <div className="flex items-center gap-2 mt-0.5">
                    {evt.severity && (
                      <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium text-white ${
                        evt.severity === 'critical' ? 'bg-red-500' :
                        evt.severity === 'high' ? 'bg-orange-500' :
                        evt.severity === 'medium' ? 'bg-yellow-500' : 'bg-green-500'
                      }`}>{evt.severity}</span>
                    )}
                    {evt.complaint_id && (
                      <Link to={`/complaints/${evt.complaint_id}`} className="text-blue-500 hover:underline text-[10px]">
                        View →
                      </Link>
                    )}
                    <span className="text-[10px] text-gray-400 dark:text-gray-500 ml-auto">
                      {evt.timestamp.toLocaleTimeString()}
                    </span>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
