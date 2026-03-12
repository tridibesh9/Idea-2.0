import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  AlertCircle,
  Clock,
  TrendingDown,
  MessageSquare,
  ShieldAlert,
} from 'lucide-react';
import { getAnalyticsSummary, getComplaints } from '../api';
import { SkeletonKPIs, SkeletonTable } from '../components/Skeleton';
import LiveFeed from '../components/LiveFeed';

const SEVERITY_COLORS = {
  critical: '#ef4444',
  high: '#f97316',
  medium: '#eab308',
  low: '#22c55e',
};

const STATUS_COLORS = {
  new: '#3b82f6',
  open: '#8b5cf6',
  in_progress: '#f59e0b',
  escalated: '#ef4444',
  resolved: '#22c55e',
  closed: '#6b7280',
};

export default function Dashboard() {
  const [summary, setSummary] = useState(null);
  const [recentComplaints, setRecentComplaints] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function load() {
      try {
        const [sumRes, compRes] = await Promise.all([
          getAnalyticsSummary(),
          getComplaints({ page: 1, page_size: 10 }),
        ]);
        setSummary(sumRes.data);
        setRecentComplaints(compRes.data.items);
      } catch (err) {
        setError('Failed to load dashboard. Is the backend running?');
        console.error('Failed to load dashboard:', err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return (
      <div>
        <h2 className="text-2xl font-bold text-gray-800 dark:text-gray-100 mb-6">Dashboard</h2>
        <SkeletonKPIs count={5} />
        <div className="mt-8">
          <SkeletonTable rows={5} cols={7} />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-center">
        <AlertCircle size={40} className="text-red-400 mb-3" />
        <p className="text-gray-600 dark:text-gray-400">{error}</p>
        <button onClick={() => window.location.reload()} className="mt-3 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700">
          Retry
        </button>
      </div>
    );
  }

  const kpis = [
    { label: 'Open Complaints', value: summary?.total_open ?? 0, icon: MessageSquare, color: 'text-blue-600', bg: 'bg-blue-50 dark:bg-blue-900/30' },
    { label: 'Critical', value: summary?.total_critical ?? 0, icon: AlertCircle, color: 'text-red-600', bg: 'bg-red-50 dark:bg-red-900/30' },
    { label: 'SLA Breached', value: summary?.total_sla_breached ?? 0, icon: ShieldAlert, color: 'text-orange-600', bg: 'bg-orange-50 dark:bg-orange-900/30' },
    { label: 'Avg Resolution (hrs)', value: summary?.avg_resolution_hours ?? '—', icon: Clock, color: 'text-green-600', bg: 'bg-green-50 dark:bg-green-900/30' },
    { label: 'Avg Sentiment', value: summary?.avg_sentiment ?? '—', icon: TrendingDown, color: 'text-purple-600', bg: 'bg-purple-50 dark:bg-purple-900/30' },
  ];

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-800 dark:text-gray-100 mb-6">Dashboard</h2>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4 mb-8">
        {kpis.map((kpi) => (
          <div key={kpi.label} className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border dark:border-gray-700 p-4">
            <div className="flex items-center gap-3">
              <div className={`p-2 rounded-lg ${kpi.bg}`}>
                <kpi.icon size={20} className={kpi.color} />
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{kpi.value}</p>
                <p className="text-xs text-gray-500 dark:text-gray-400">{kpi.label}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Complaints */}
        <div className="lg:col-span-2 bg-white dark:bg-gray-800 rounded-xl shadow-sm border dark:border-gray-700">
          <div className="p-4 border-b dark:border-gray-700 flex items-center justify-between">
            <h3 className="font-semibold text-gray-800 dark:text-gray-200">Recent Complaints</h3>
            <Link to="/complaints" className="text-sm text-blue-600 dark:text-blue-400 hover:underline">
              View All →
            </Link>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 dark:bg-gray-700/50">
                <tr>
                  <th className="text-left p-3 font-medium text-gray-600 dark:text-gray-300">Channel</th>
                  <th className="text-left p-3 font-medium text-gray-600 dark:text-gray-300">Subject</th>
                  <th className="text-left p-3 font-medium text-gray-600 dark:text-gray-300">Severity</th>
                  <th className="text-left p-3 font-medium text-gray-600 dark:text-gray-300">Status</th>
                  <th className="text-left p-3 font-medium text-gray-600 dark:text-gray-300">Date</th>
                </tr>
              </thead>
              <tbody>
                {recentComplaints.map((c) => (
                  <tr key={c.id} className="border-t dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/50 cursor-pointer" onClick={() => window.location.href = `/complaints/${c.id}`}>
                    <td className="p-3">
                      <span className="px-2 py-1 rounded-full text-xs bg-gray-100 dark:bg-gray-700 font-medium dark:text-gray-300">
                        {c.channel}
                      </span>
                    </td>
                    <td className="p-3 text-gray-800 dark:text-gray-200 max-w-xs truncate">{c.subject || c.body?.slice(0, 60)}</td>
                    <td className="p-3">
                      <span
                        className="px-2 py-1 rounded-full text-xs font-medium text-white"
                        style={{ backgroundColor: SEVERITY_COLORS[c.severity] || '#6b7280' }}
                      >
                        {c.severity}
                      </span>
                    </td>
                    <td className="p-3">
                      <span
                        className="px-2 py-1 rounded-full text-xs font-medium text-white"
                        style={{ backgroundColor: STATUS_COLORS[c.status] || '#6b7280' }}
                      >
                        {c.status}
                      </span>
                    </td>
                    <td className="p-3 text-gray-500 dark:text-gray-400 text-xs">
                      {new Date(c.created_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
                {recentComplaints.length === 0 && (
                  <tr>
                    <td colSpan={5} className="p-8 text-center text-gray-400 dark:text-gray-500">
                      No complaints yet. Submit one to get started!
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Live Feed */}
        <div>
          <LiveFeed />
        </div>
      </div>
    </div>
  );
}
